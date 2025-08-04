#pragma once
#include "renderware_handler.h"
#include <vector>
#include <memory>
#include <string>
#include <map>

// Main Renderware Modding Suite Backend
class RenderwareModdingSuite {
private:
    std::vector<std::unique_ptr<RenderwareHandler>> handlers;
    std::map<std::string, size_t> commandToHandlerMap;
    
    void initializeHandlers();
    void setupCommandMapping();
    
public:
    RenderwareModdingSuite();
    ~RenderwareModdingSuite() = default;
    
    void listSupportedFormats() const;
    bool processFile(const std::string& command, const std::string& filename);
    void showHelp(const std::string& programName) const;
    bool runTest() const;
    
    // Get handler by file extension
    RenderwareHandler* getHandlerByExtension(const std::string& extension) const;
    
    // Get all supported extensions
    std::vector<std::string> getSupportedExtensions() const;
};
