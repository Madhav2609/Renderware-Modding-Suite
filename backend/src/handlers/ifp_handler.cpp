#include "ifp_handler.h"
#include <iostream>

bool IFPAnimationHandler::load(const std::string& filename) {
    std::cout << "Loading IFP animation: " << filename << std::endl;
    // TODO: Implement IFP loading logic
    return true;
}

bool IFPAnimationHandler::save(const std::string& filename) {
    std::cout << "Saving IFP animation: " << filename << std::endl;
    // TODO: Implement IFP saving logic
    return true;
}

std::string IFPAnimationHandler::getFormatInfo() const {
    return "IFP - RenderWare Animation File";
}

std::string IFPAnimationHandler::getFileExtension() const {
    return ".ifp";
}
