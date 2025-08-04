#include <iostream>
#include <string>
#include "main_application.h"

int main(int argc, char* argv[]) {
    std::cout << "Renderware Modding Suite Backend v1.0" << std::endl;
    std::cout << "Supporting GTA III, Vice City, and San Andreas" << std::endl;
    std::cout << "=============================================" << std::endl;
    
    RenderwareModdingSuite suite;
    
    if (argc == 1) {
        // No arguments - show help
        suite.showHelp(argv[0]);
        return 0;
    }
    
    std::string command = argv[1];
    
    if (command == "formats") {
        suite.listSupportedFormats();
    } else if (command == "test") {
        suite.runTest();
    } else if (argc >= 3) {
        std::string filename = argv[2];
        bool success = suite.processFile(command, filename);
        return success ? 0 : 1;
    } else {
        std::cout << "Error: Command '" << command << "' requires a filename." << std::endl;
        return 1;
    }
    
    return 0;
}
