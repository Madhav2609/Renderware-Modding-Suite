#include "ide_handler.h"
#include <iostream>

bool IDEDefinitionHandler::load(const std::string& filename) {
    std::cout << "Loading IDE definitions: " << filename << std::endl;
    // TODO: Implement IDE loading logic
    return true;
}

bool IDEDefinitionHandler::save(const std::string& filename) {
    std::cout << "Saving IDE definitions: " << filename << std::endl;
    // TODO: Implement IDE saving logic
    return true;
}

std::string IDEDefinitionHandler::getFormatInfo() const {
    return "IDE - Item Definition File";
}

std::string IDEDefinitionHandler::getFileExtension() const {
    return ".ide";
}
