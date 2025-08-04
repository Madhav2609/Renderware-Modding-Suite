#include "dff_handler.h"
#include <iostream>

bool DFFModelHandler::load(const std::string& filename) {
    std::cout << "Loading DFF model: " << filename << std::endl;
    // TODO: Implement DFF loading logic
    return true;
}

bool DFFModelHandler::save(const std::string& filename) {
    std::cout << "Saving DFF model: " << filename << std::endl;
    // TODO: Implement DFF saving logic
    return true;
}

std::string DFFModelHandler::getFormatInfo() const {
    return "DFF - RenderWare 3D Model Format";
}

std::string DFFModelHandler::getFileExtension() const {
    return ".dff";
}
