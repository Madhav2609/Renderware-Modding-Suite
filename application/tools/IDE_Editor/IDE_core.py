# IDE_core.py

import json

class IDEParser:
    """
    Parses an IDE file based on a provided JSON schema.
    This class contains no GUI-related code.
    """
    def __init__(self, schema):
        self.schema = schema["sections"]

    def parse(self, file_content):
        """
        Parses the entire content of an IDE file.

        Args:
            file_content (str): The string content of the IDE file.

        Returns:
            dict: A dictionary representing the parsed data, structured by sections.
        """
        lines = file_content.splitlines()
        parsed_data = {}
        current_section = None
        
        # Ensure all sections from schema exist in the model for consistency
        for section_key in self.schema.keys():
            parsed_data[section_key] = {"rows": [], "errors": []}

        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            # Check for section headers
            if line.lower() in self.schema:
                current_section = line.lower()
                # The section is already initialized, so we just set the context
                continue
            
            # Check for section end
            if line.lower() == 'end':
                current_section = None
                continue

            # If we are inside a known section, parse the row
            if current_section:
                self._parse_row(line, current_section, parsed_data)
        
        # Return all sections (even empty) so the UI can render them
        return parsed_data


    def _parse_row(self, line, section_key, parsed_data):
        """Parses a single row within a section."""
        clean_line = line.split('#', 1)[0].strip()
        tokens = [token.strip() for token in clean_line.split(',') if token.strip()]

        if not tokens:
            return

        schema_section = self.schema.get(section_key)
        if not schema_section:
            # Should not happen if current_section is a valid key
            return

        row_data = {}
        token_index = 0
        columns = schema_section.get("columns", [])

        # A simple placeholder for handling complex sections like 2dfx or path
        if not columns and schema_section.get("parseHints", {}).get("note"):
            row_data['raw'] = line # Store the raw line
            parsed_data[section_key]["rows"].append(row_data)
            return

        col_index = 0
        while col_index < len(columns) and token_index < len(tokens):
            col_schema = columns[col_index]
            col_name = col_schema["name"]
            col_type = col_schema["type"]

            try:
                # Handle variable length arrays like 'drawDists'
                if col_type == "array":
                    count = 1
                    count_key = col_schema.get("dependsOn")
                    if count_key and count_key in row_data:
                        # Ensure the dependent value is a valid integer
                        try:
                            count = int(row_data[count_key])
                        except (ValueError, TypeError):
                            count = 1 # Fallback
                    
                    # Ensure we don't read past the end of the tokens
                    end_slice = min(token_index + count, len(tokens))
                    array_tokens = tokens[token_index : end_slice]

                    if col_schema["itemsType"] == "float":
                        row_data[col_name] = [float(t) for t in array_tokens]
                    else: # Assume int if not float
                        row_data[col_name] = [int(t) for t in array_tokens]
                    token_index += len(array_tokens)
                
                # Handle simple types
                else:
                    token = tokens[token_index]
                    if col_type == "int":
                        row_data[col_name] = int(token)
                    elif col_type == "float":
                        row_data[col_name] = float(token)
                    else: # string
                        row_data[col_name] = token
                    token_index += 1
            except (ValueError, IndexError) as e:
                error_msg = f"Error parsing column '{col_name}' in line: '{line}'. Reason: {e}"
                parsed_data[section_key]["errors"].append(error_msg)
                # On error, we still advance the column to be resilient
                col_index += 1
                continue

            col_index += 1
        
        # Store any leftover tokens
        if token_index < len(tokens):
            row_data['extraFields'] = tokens[token_index:]

        parsed_data[section_key]["rows"].append(row_data)

    def serialize(self, parsed_data):
        """
        Converts parsed data back to IDE file format.
        
        Args:
            parsed_data (dict): The parsed data structure
            
        Returns:
            str: The serialized IDE file content
        """
        lines = []
        
        for section_key in self.schema.keys():
            section_data = parsed_data.get(section_key, {"rows": []})
            rows = section_data.get("rows", [])
            
            if not rows:
                continue
                
            # Add section header
            lines.append(section_key)
            
            # Serialize each row
            for row_data in rows:
                serialized_row = self._serialize_row(row_data, section_key)
                if serialized_row:
                    lines.append(serialized_row)
            
            # Add section end
            lines.append("end")
            lines.append("")  # Empty line after section
        
        return "\n".join(lines)
    
    def _serialize_row(self, row_data, section_key):
        """Serialize a single row back to IDE format."""
        schema_section = self.schema.get(section_key)
        if not schema_section:
            return row_data.get('raw', '')
        
        # Handle raw sections (like path)
        if 'raw' in row_data:
            return row_data['raw']
        
        tokens = []
        columns = schema_section.get("columns", [])
        
        # Handle 2dfx sections with commonPrefix and types
        if schema_section.get("commonPrefix"):
            # Add common prefix fields
            for col in schema_section["commonPrefix"]:
                value = row_data.get(col["name"])
                if value is not None:
                    tokens.append(str(value))
            
            # Add type-specific fields
            effect_type = row_data.get("type")
            if effect_type and str(effect_type) in schema_section.get("types", {}):
                type_schema = schema_section["types"][str(effect_type)]
                for col in type_schema.get("columns", []):
                    value = row_data.get(col["name"])
                    if value is not None:
                        tokens.append(str(value))
        
        # Handle regular columns
        elif columns:
            for col in columns:
                col_name = col["name"]
                col_type = col["type"]
                value = row_data.get(col_name)
                
                if value is None:
                    continue
                
                if col_type == "array":
                    # Handle array fields like drawDists
                    if isinstance(value, list):
                        tokens.extend([str(v) for v in value])
                    else:
                        tokens.append(str(value))
                else:
                    tokens.append(str(value))
        
        # Add any extra fields that were preserved
        extra_fields = row_data.get('extraFields', [])
        if extra_fields:
            tokens.extend([str(field) for field in extra_fields])
        
        return ", ".join(tokens) if tokens else ""

    def validate_single_file(self, parsed_data, file_path=""):
        """
        Validate a single IDE file for duplicate IDs and model names.
        
        Args:
            parsed_data (dict): The parsed data structure
            file_path (str): Path to the file being validated
            
        Returns:
            dict: Validation results with errors and warnings
        """
        results = {
            "file_path": file_path,
            "errors": [],
            "warnings": [],
            "duplicate_ids": {},
            "duplicate_models": {},
            "stats": {}
        }
        
        # Track IDs and model names across all sections
        all_ids = {}  # id -> [(section, row_index)]
        all_models = {}  # model_name -> [(section, row_index)]
        
        for section_key, section_data in parsed_data.items():
            rows = section_data.get("rows", [])
            results["stats"][section_key] = len(rows)
            
            schema_section = self.schema.get(section_key, {})
            primary_keys = schema_section.get("primaryKeys", [])
            
            for row_idx, row_data in enumerate(rows):
                # Check for duplicate IDs
                if "id" in primary_keys and "id" in row_data:
                    obj_id = row_data["id"]
                    if obj_id in all_ids:
                        all_ids[obj_id].append((section_key, row_idx))
                    else:
                        all_ids[obj_id] = [(section_key, row_idx)]
                
                # Check for duplicate model names
                model_field = None
                for field in ["modelName", "model"]:
                    if field in row_data:
                        model_field = field
                        break
                
                if model_field:
                    model_name = row_data[model_field]
                    if model_name in all_models:
                        all_models[model_name].append((section_key, row_idx))
                    else:
                        all_models[model_name] = [(section_key, row_idx)]
        
        # Report duplicates
        for obj_id, locations in all_ids.items():
            if len(locations) > 1:
                results["duplicate_ids"][obj_id] = locations
                results["errors"].append(f"Duplicate ID {obj_id} found in sections: {', '.join([f'{sec}[{idx}]' for sec, idx in locations])}")
        
        for model_name, locations in all_models.items():
            if len(locations) > 1:
                results["duplicate_models"][model_name] = locations
                results["warnings"].append(f"Duplicate model '{model_name}' found in sections: {', '.join([f'{sec}[{idx}]' for sec, idx in locations])}")
        
        return results
    
    def validate_multiple_files(self, file_data_models):
        """
        Validate multiple IDE files for cross-file duplicate IDs and models.
        
        Args:
            file_data_models (dict): Maps file_path -> parsed_data
            
        Returns:
            dict: Comprehensive validation results
        """
        results = {
            "files": {},
            "cross_file_duplicates": {
                "ids": {},
                "models": {}
            },
            "summary": {
                "total_files": len(file_data_models),
                "files_with_errors": 0,
                "total_errors": 0,
                "total_warnings": 0
            }
        }
        
        # Global tracking across all files
        global_ids = {}  # id -> [(file_path, section, row_index)]
        global_models = {}  # model_name -> [(file_path, section, row_index)]
        
        # Validate each file individually
        for file_path, parsed_data in file_data_models.items():
            file_results = self.validate_single_file(parsed_data, file_path)
            results["files"][file_path] = file_results
            
            if file_results["errors"]:
                results["summary"]["files_with_errors"] += 1
            
            results["summary"]["total_errors"] += len(file_results["errors"])
            results["summary"]["total_warnings"] += len(file_results["warnings"])
            
            # Collect for cross-file validation
            for section_key, section_data in parsed_data.items():
                rows = section_data.get("rows", [])
                schema_section = self.schema.get(section_key, {})
                primary_keys = schema_section.get("primaryKeys", [])
                
                for row_idx, row_data in enumerate(rows):
                    # Track IDs globally
                    if "id" in primary_keys and "id" in row_data:
                        obj_id = row_data["id"]
                        if obj_id in global_ids:
                            global_ids[obj_id].append((file_path, section_key, row_idx))
                        else:
                            global_ids[obj_id] = [(file_path, section_key, row_idx)]
                    
                    # Track model names globally
                    model_field = None
                    for field in ["modelName", "model"]:
                        if field in row_data:
                            model_field = field
                            break
                    
                    if model_field:
                        model_name = row_data[model_field]
                        if model_name in global_models:
                            global_models[model_name].append((file_path, section_key, row_idx))
                        else:
                            global_models[model_name] = [(file_path, section_key, row_idx)]
        
        # Find cross-file duplicates
        for obj_id, locations in global_ids.items():
            if len(locations) > 1:
                # Check if duplicates are across different files
                files_involved = set(loc[0] for loc in locations)
                if len(files_involved) > 1:
                    results["cross_file_duplicates"]["ids"][obj_id] = locations
        
        for model_name, locations in global_models.items():
            if len(locations) > 1:
                files_involved = set(loc[0] for loc in locations)
                if len(files_involved) > 1:
                    results["cross_file_duplicates"]["models"][model_name] = locations
        
        return results