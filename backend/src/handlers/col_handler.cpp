#include "col_handler.h"
#include <iostream>

bool COLCollisionHandler::load(const std::string& filename) {
    std::cout << "Loading COL collision data: " << filename << std::endl;
    // TODO: Implement COL loading logic
    return true;
}

bool COLCollisionHandler::save(const std::string& filename) {
    std::cout << "Saving COL collision data: " << filename << std::endl;
    // TODO: Implement COL saving logic
    return true;
}

std::string COLCollisionHandler::getFormatInfo() const {
    return "COL - RenderWare Collision Data";
}

std::string COLCollisionHandler::getFileExtension() const {
    return ".col";
}
