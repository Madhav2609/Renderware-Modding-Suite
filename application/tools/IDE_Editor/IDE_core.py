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