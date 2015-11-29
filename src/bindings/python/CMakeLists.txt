#
# This file is part of USBProxy.
#

project(libusbproxyAPI C)
set(PACKAGE libusbproxyAPI)

include_directories(${libusbproxy_SOURCE_DIR} ${usbproxy_filters_SOURCE_DIR} ${usbproxy_devices_SOURCE_DIR})

set(python_scripts
	${CMAKE_CURRENT_SOURCE_DIR}/deviceproxy.py
	${CMAKE_CURRENT_SOURCE_DIR}/filters.py
	${CMAKE_CURRENT_SOURCE_DIR}/kbd.py
	${CMAKE_CURRENT_SOURCE_DIR}/keymap.py
	${CMAKE_CURRENT_SOURCE_DIR}/ubertooth.py
	${CMAKE_CURRENT_SOURCE_DIR}/USBClass.py
	${CMAKE_CURRENT_SOURCE_DIR}/USBConfiguration.py
	${CMAKE_CURRENT_SOURCE_DIR}/USBDevice.py
	${CMAKE_CURRENT_SOURCE_DIR}/USBEndpoint.py
	${CMAKE_CURRENT_SOURCE_DIR}/USBInterface.py
	${CMAKE_CURRENT_SOURCE_DIR}/USBKeyboard.py
	${CMAKE_CURRENT_SOURCE_DIR}/USBMassStorage.py
	${CMAKE_CURRENT_SOURCE_DIR}/USBProxyApp.py
	${CMAKE_CURRENT_SOURCE_DIR}/usbproxy-fd-keyboard.py
	${CMAKE_CURRENT_SOURCE_DIR}/usbproxy-fd-umass.py
	${CMAKE_CURRENT_SOURCE_DIR}/usbproxy.py
	${CMAKE_CURRENT_SOURCE_DIR}/USB.py
	${CMAKE_CURRENT_SOURCE_DIR}/USBVendor.py
	CACHE INTERNAL "List of python scripts")

# Target
set(cpp_sources
	${CMAKE_CURRENT_SOURCE_DIR}/API.cpp
	CACHE INTERNAL "List of CPP sources")

add_definitions( -DPLUGIN_PATH="${CMAKE_INSTALL_PREFIX}/lib/USBProxy/")

# Dynamic library
add_library(USBProxyAPI SHARED ${cpp_sources})

set_source_files_properties(${cpp_sources} PROPERTIES COMPILE_FLAGS  "-std=c++11 -pthread -Wall")

#set_target_properties(USBProxyAPI PROPERTIES VERSION ${MAJOR_VERSION}.${MINOR_VERSION} SOVERSION 0)

target_link_libraries(USBProxyAPI USBProxy)

install(TARGETS USBProxyAPI
        LIBRARY DESTINATION lib${LIB_SUFFIX}
        COMPONENT sharedlibs
        )
install(FILES ${python_scripts}
	DESTINATION bindings/python/USBProxy
	COMPONENT pythonScripts
	PERMISSIONS OWNER_EXECUTE OWNER_WRITE OWNER_READ
	)
