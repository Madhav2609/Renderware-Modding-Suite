#include "txd_handler.h"
#include <iostream>

bool TXDTextureHandler::load(const std::string& filename) {
    std::cout << "Loading TXD texture dictionary: " << filename << std::endl;
    // TODO: Implement TXD loading logic
    return true;
}

bool TXDTextureHandler::save(const std::string& filename) {
    std::cout << "Saving TXD texture dictionary: " << filename << std::endl;
    // TODO: Implement TXD saving logic
    return true;
}

std::string TXDTextureHandler::getFormatInfo() const {
    return "TXD - RenderWare Texture Dictionary";
}

std::string TXDTextureHandler::getFileExtension() const {
    return ".txd";
}
