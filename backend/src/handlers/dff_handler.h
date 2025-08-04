#pragma once
#include "../renderware_handler.h"

// DFF Model Handler (3D Models)
class DFFModelHandler : public RenderwareHandler {
public:
    bool load(const std::string& filename) override;
    bool save(const std::string& filename) override;
    std::string getFormatInfo() const override;
    std::string getFileExtension() const override;
};
