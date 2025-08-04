#pragma once
#include <string>

// Base class for all Renderware format handlers
class RenderwareHandler {
public:
    virtual ~RenderwareHandler() = default;
    virtual bool load(const std::string& filename) = 0;
    virtual bool save(const std::string& filename) = 0;
    virtual std::string getFormatInfo() const = 0;
    virtual std::string getFileExtension() const = 0;
};
