cmake_minimum_required(VERSION 3.10)
project(go2_taller)

set(CMAKE_CXX_STANDARD 17)

# Ruta al SDK de Unitree
set(UNITREE_SDK_PATH "${CMAKE_CURRENT_SOURCE_DIR}/../../../../00SDK/unitree_sdk2")

# Incluir headers del SDK
include_directories(
    ${UNITREE_SDK_PATH}/include
    ${UNITREE_SDK_PATH}/thirdparty/include
    ${UNITREE_SDK_PATH}/thirdparty/include/ddscxx
)

# Detectar arquitectura
if(CMAKE_SYSTEM_PROCESSOR STREQUAL "aarch64")
    set(SDK_ARCH "aarch64")
    set(SDK_LIB_DIR ${UNITREE_SDK_PATH}/lib/aarch64)
else()
    set(SDK_ARCH "x86_64")
    set(SDK_LIB_DIR ${UNITREE_SDK_PATH}/lib/x86_64)
endif()

find_library(UNITREE_SDK2_LIB unitree_sdk2 PATHS ${SDK_LIB_DIR} NO_DEFAULT_PATH)
find_library(DDSC_LIB         ddsc         PATHS ${UNITREE_SDK_PATH}/thirdparty/lib/${SDK_ARCH} NO_DEFAULT_PATH)
find_library(DDSCXX_LIB       ddscxx       PATHS ${UNITREE_SDK_PATH}/thirdparty/lib/${SDK_ARCH} NO_DEFAULT_PATH)

if(NOT UNITREE_SDK2_LIB)
    message(FATAL_ERROR "No se encontró libunitree_sdk2 en ${SDK_LIB_DIR}")
endif()

add_executable(go2_taller taller.cpp)

target_link_libraries(go2_taller
    ${UNITREE_SDK2_LIB}
    ${DDSCXX_LIB}
    ${DDSC_LIB}
    pthread
)

# RPATH para que encuentre las .so en tiempo de ejecución
set_target_properties(go2_taller PROPERTIES
    BUILD_RPATH "${UNITREE_SDK_PATH}/thirdparty/lib/${SDK_ARCH}"
    INSTALL_RPATH "${UNITREE_SDK_PATH}/thirdparty/lib/${SDK_ARCH}"
)
