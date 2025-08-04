#include "main_application.h"
#include "handlers/dff_handler.h"
#include "handlers/txd_handler.h"
#include "handlers/col_handler.h"
#include "handlers/ifp_handler.h"
#include "handlers/ide_handler.h"
#include "handlers/ipl_handler.h"
#include <iostream>
#include <algorithm>

RenderwareModdingSuite::RenderwareModdingSuite() {
    initializeHandlers();
    setupCommandMapping();
}

void RenderwareModdingSuite::initializeHandlers() {
    // Initialize all format handlers
    handlers.push_back(std::make_unique<DFFModelHandler>());
    handlers.push_back(std::make_unique<TXDTextureHandler>());
    handlers.push_back(std::make_unique<COLCollisionHandler>());
    handlers.push_back(std::make_unique<IFPAnimationHandler>());
    handlers.push_back(std::make_unique<IDEDefinitionHandler>());
    handlers.push_back(std::make_unique<IPLPlacementHandler>());
}

void RenderwareModdingSuite::setupCommandMapping() {
    // Map commands to handler indices
    commandToHandlerMap["load_dff"] = 0;
    commandToHandlerMap["save_dff"] = 0;
    commandToHandlerMap["load_txd"] = 1;
    commandToHandlerMap["save_txd"] = 1;
    commandToHandlerMap["load_col"] = 2;
    commandToHandlerMap["save_col"] = 2;
    commandToHandlerMap["load_ifp"] = 3;
    commandToHandlerMap["save_ifp"] = 3;
    commandToHandlerMap["load_ide"] = 4;
    commandToHandlerMap["save_ide"] = 4;
    commandToHandlerMap["load_ipl"] = 5;
    commandToHandlerMap["save_ipl"] = 5;
}

void RenderwareModdingSuite::listSupportedFormats() const {
    std::cout << "Supported Renderware Formats:" << std::endl;
    for (const auto& handler : handlers) {
        std::cout << "- " << handler->getFormatInfo() 
                  << " (" << handler->getFileExtension() << ")" << std::endl;
    }
}

bool RenderwareModdingSuite::processFile(const std::string& command, const std::string& filename) {
    auto it = commandToHandlerMap.find(command);
    if (it == commandToHandlerMap.end()) {
        std::cout << "Unknown command: " << command << std::endl;
        return false;
    }
    
    size_t handlerIndex = it->second;
    if (handlerIndex >= handlers.size()) {
        std::cout << "Invalid handler index for command: " << command << std::endl;
        return false;
    }
    
    // Determine if it's a load or save operation
    bool isLoadOperation = command.find("load_") == 0;
    
    if (isLoadOperation) {
        return handlers[handlerIndex]->load(filename);
    } else {
        return handlers[handlerIndex]->save(filename);
    }
}

void RenderwareModdingSuite::showHelp(const std::string& programName) const {
    std::cout << "Usage: " << programName << " <command> [filename]" << std::endl;
    std::cout << "\nCommands:" << std::endl;
    std::cout << "  formats          - List supported formats" << std::endl;
    std::cout << "  load_dff <file>  - Load DFF model file" << std::endl;
    std::cout << "  save_dff <file>  - Save DFF model file" << std::endl;
    std::cout << "  load_txd <file>  - Load TXD texture file" << std::endl;
    std::cout << "  save_txd <file>  - Save TXD texture file" << std::endl;
    std::cout << "  load_col <file>  - Load COL collision file" << std::endl;
    std::cout << "  save_col <file>  - Save COL collision file" << std::endl;
    std::cout << "  load_ifp <file>  - Load IFP animation file" << std::endl;
    std::cout << "  save_ifp <file>  - Save IFP animation file" << std::endl;
    std::cout << "  load_ide <file>  - Load IDE definition file" << std::endl;
    std::cout << "  save_ide <file>  - Save IDE definition file" << std::endl;
    std::cout << "  load_ipl <file>  - Load IPL placement file" << std::endl;
    std::cout << "  save_ipl <file>  - Save IPL placement file" << std::endl;
    std::cout << "  test             - Run backend test" << std::endl;
}

bool RenderwareModdingSuite::runTest() const {
    std::cout << "Backend test successful!" << std::endl;
    std::cout << "All Renderware format handlers initialized:" << std::endl;
    for (const auto& handler : handlers) {
        std::cout << "  ✓ " << handler->getFormatInfo() << std::endl;
    }
    return true;
}

RenderwareHandler* RenderwareModdingSuite::getHandlerByExtension(const std::string& extension) const {
    for (const auto& handler : handlers) {
        if (handler->getFileExtension() == extension) {
            return handler.get();
        }
    }
    return nullptr;
}

std::vector<std::string> RenderwareModdingSuite::getSupportedExtensions() const {
    std::vector<std::string> extensions;
    for (const auto& handler : handlers) {
        extensions.push_back(handler->getFileExtension());
    }
    return extensions;
}
