#include "ipl_handler.h"
#include <iostream>

bool IPLPlacementHandler::load(const std::string& filename) {
    std::cout << "Loading IPL placements: " << filename << std::endl;
    // TODO: Implement IPL loading logic
    return true;
}

bool IPLPlacementHandler::save(const std::string& filename) {
    std::cout << "Saving IPL placements: " << filename << std::endl;
    // TODO: Implement IPL saving logic
    return true;
}

std::string IPLPlacementHandler::getFormatInfo() const {
    return "IPL - Item Placement File";
}

std::string IPLPlacementHandler::getFileExtension() const {
    return ".ipl";
}
