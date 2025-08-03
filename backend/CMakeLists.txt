cmake_minimum_required(VERSION 3.15)
project(RenderwareModdingSuite VERSION 1.0.0)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Compiler-specific options
if(MSVC)
    add_compile_options(/W4)
else()
    add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Create source files list
set(SOURCES
    src/main.cpp
)

# Create headers list (for future use)
set(HEADERS
    # Will add header files here as we develop
)

# Add executable
add_executable(renderware_backend ${SOURCES} ${HEADERS})

# Set output directory
set_target_properties(renderware_backend PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
)

# Optional: Add pybind11 for Python bindings (future enhancement)
# find_package(pybind11 REQUIRED)
# pybind11_add_module(renderware_bindings src/python_bindings.cpp)

# Installation rules
install(TARGETS renderware_backend
    RUNTIME DESTINATION bin
)

# Print build information
message(STATUS "Building Renderware Modding Suite Backend")
message(STATUS "Version: ${PROJECT_VERSION}")
message(STATUS "C++ Standard: ${CMAKE_CXX_STANDARD}")
message(STATUS "Build Type: ${CMAKE_BUILD_TYPE}")
