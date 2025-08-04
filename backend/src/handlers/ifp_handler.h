#pragma once
#include "../renderware_handler.h"

// IFP Animation Handler
class IFPAnimationHandler : public RenderwareHandler {
public:
    bool load(const std::string& filename) override;
    bool save(const std::string& filename) override;
    std::string getFormatInfo() const override;
    std::string getFileExtension() const override;
};
