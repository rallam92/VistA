#---------------------------------------------------------------------------
# Copyright 2011 The Open Source Electronic Health Record Agent
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#---------------------------------------------------------------------------

if(POLICY CMP0012)
  cmake_policy(SET CMP0012 NEW)
endif()

find_package(Java REQUIRED)
include(UseJava)

find_program(DOT_EXECUTABLE NAMES dot REQUIRED)

set(DOCUMENT_VISTA_M_DIR "" CACHE PATH
  "Path to the folder that contains the routines and globals from OSEHRA")
if(NOT EXISTS ${DOCUMENT_VISTA_M_DIR})
  message(WARNING "DOCUMENT_VISTA_M_DIR is required.")
endif()

set(DOCUMENT_VISTA_OUTPUT_DIR "" CACHE PATH
  "Path to the directory where ViViaN and DOX files will be generated")
file(MAKE_DIRECTORY "${DOCUMENT_VISTA_OUTPUT_DIR}")
if(NOT EXISTS ${DOCUMENT_VISTA_OUTPUT_DIR})
  message(WARNING "DOCUMENT_VISTA_OUTPUT_DIR is required.")
endif()

set(ICR_FILE "" CACHE FILEPATH "ICR File from http://foia-vista.osehra.org/VistA_Integration_Agreement/")
if(NOT EXISTS ${ICR_FILE})
  message(WARNING "ICR_FILE is required.")
endif()

set(PYTHONSCRIPTS_DIR "${CMAKE_CURRENT_SOURCE_DIR}/PythonScripts")

set(GENERATE_DOX "TRUE" CACHE BOOL "Generate the DOX pages")
mark_as_advanced(GENERATE_DOX)

set(GENERATE_VIVIAN "TRUE" CACHE BOOL "Generate ViViaN data")
mark_as_advanced(GENERATE_VIVIAN)

if (NOT GENERATE_DOX AND NOT GENERATE_VIVIAN)
  message(ERROR "Must select GENERATE_DOX and/or GENERATE_VIVIAN.")
endif()

set(SCRIPT_OUTPUT_DIR "${CMAKE_BINARY_DIR}/Docs/CallerGraph")

# 1. Generate XINDEX based cross reference output used by WebPageGenerator (DOX)
if (GENERATE_DOX)
  file(GLOB PACKAGES ${DOCUMENT_VISTA_M_DIR}/Packages/*)
  set(CALLER_GRAPH_LOG_DIR "${SCRIPT_OUTPUT_DIR}/Log")
  file(MAKE_DIRECTORY "${CALLER_GRAPH_LOG_DIR}")
  foreach(package ${PACKAGES})
    get_filename_component(package_name ${package} NAME)
    if(IS_DIRECTORY ${package})
      file(GLOB routines "${package}/Routines/*.m")
      set(AllRoutines "")
      foreach(routine ${routines})
        get_filename_component(routine_name ${routine} NAME_WE)
        set(AllRoutines "${AllRoutines}AllRoutines.append(\"${routine_name}\")\n")
      endforeach()
      string(REPLACE  " " "_" package_file_name "${package_name}")
      set(logfile "${CALLER_GRAPH_LOG_DIR}/${package_file_name}.log")
      #Configures the python script with the name of the routine
      configure_file(${CMAKE_CURRENT_SOURCE_DIR}/XindexCallerGraph.py.in
                     ${SCRIPT_OUTPUT_DIR}/${package_file_name}.py)

      configure_file(${CMAKE_CURRENT_SOURCE_DIR}/XindexCallerGraph.cmake.in
                     ${SCRIPT_OUTPUT_DIR}/${package_file_name}.cmake @ONLY)

      # Creates the command that will be called for the Test
      add_test(CALLERGRAPH_${package_file_name} ${CMAKE_COMMAND} -P ${SCRIPT_OUTPUT_DIR}/${package_file_name}.cmake)
    endif()
  endforeach()
endif()

# 2. Generate Fileman Schema used by WebPageGenerator (DOX)
if (GENERATE_DOX)
  set(FILEMAN_SCHEMA_DIR "${CMAKE_BINARY_DIR}/Docs/Schema")
  configure_file(${CMAKE_CURRENT_SOURCE_DIR}/FileManGlobalAttributes.py.in ${SCRIPT_OUTPUT_DIR}/FilemanGlobalAttributes.py)
  configure_file(${CMAKE_CURRENT_SOURCE_DIR}/GetFilemanSchema.cmake.in ${SCRIPT_OUTPUT_DIR}/GetFilemanSchema.cmake @ONLY)
  add_test(GetFilemanSchema ${CMAKE_COMMAND} -P ${SCRIPT_OUTPUT_DIR}/GetFilemanSchema.cmake)
  set_tests_properties(GetFilemanSchema PROPERTIES TIMEOUT 7200)
  set(FILEMANDBCALL_JSON "${DOCUMENT_VISTA_OUTPUT_DIR}/filemanDBCall.json")
endif()

# 3. Download, compile and run 'M Routine Analyzer' tool
# Creates 'filemanDBCall.json', which is used by WebPageGenerator (DOX)
if (GENERATE_DOX)
  configure_file(${CMAKE_CURRENT_SOURCE_DIR}/MRoutineAnalyzer.cmake.in ${SCRIPT_OUTPUT_DIR}/MRoutineAnalyzer.cmake @ONLY)
  add_test(MRoutineAnalyzer ${CMAKE_COMMAND} -P ${SCRIPT_OUTPUT_DIR}/MRoutineAnalyzer.cmake)
  set_tests_properties(MRoutineAnalyzer
                        PROPERTIES FAIL_REGULAR_EXPRESSION "SEVERE")
endif()

# 4. Run FileMan Global Data Parser script
# Generates ViViaN data and 'Routine-Ref.json' for the WebPageGenerator (DOX)
if (GENERATE_DOX OR GENERATE_VIVIAN)
  configure_file(${CMAKE_CURRENT_SOURCE_DIR}/FileManGlobalDataParser.cmake.in ${SCRIPT_OUTPUT_DIR}/FileManGlobalDataParser.cmake @ONLY)
  add_test(FileManGlobalDataParser ${CMAKE_COMMAND} -P ${SCRIPT_OUTPUT_DIR}/FileManGlobalDataParser.cmake)
  set_tests_properties(FileManGlobalDataParser PROPERTIES TIMEOUT 9000)
endif()

# 5. Run ICR Parser Script to parse and convert the downloaded ICR text file
# to json (DOX) and html (ViViaN)
if (GENERATE_DOX OR GENERATE_VIVIAN)
  set(DOCUMENT_VISTA_ICR_OUTPUT_DIR "${DOCUMENT_VISTA_OUTPUT_DIR}/ICR")
  file(MAKE_DIRECTORY "${DOCUMENT_VISTA_ICR_OUTPUT_DIR}")
  configure_file(${CMAKE_CURRENT_SOURCE_DIR}/ICRParser.cmake.in ${SCRIPT_OUTPUT_DIR}/ICRParser.cmake @ONLY)
  add_test(ICRParser ${CMAKE_COMMAND} -P ${SCRIPT_OUTPUT_DIR}/ICRParser.cmake)
endif()

# 6. Write repository information to 'filesInfo.json' (VIVIAN)
if (GENERATE_VIVIAN)
  configure_file(${CMAKE_CURRENT_SOURCE_DIR}/GenerateRepoInfo.cmake.in ${SCRIPT_OUTPUT_DIR}/GenerateRepoInfo.cmake @ONLY)
  add_test(GenerateRepoInfo ${CMAKE_COMMAND} -P ${SCRIPT_OUTPUT_DIR}/GenerateRepoInfo.cmake)
endif()

# 7. Run the Web Page Generator script to create DOX pages
if (GENERATE_DOX)
  set(DOCUMENT_VISTA_DOX_OUTPUT_DIR "${DOCUMENT_VISTA_OUTPUT_DIR}/dox")
  file(MAKE_DIRECTORY "${DOCUMENT_VISTA_DOX_OUTPUT_DIR}")
  if(NOT "${ICR_FILE}" STREQUAL "")
    # Get file name without directory or longest extension
    get_filename_component(ICR_JSON_FILE ${ICR_FILE} NAME_WE)
    set(ICR_JSON_FILE "${DOCUMENT_VISTA_ICR_OUTPUT_DIR}/${ICR_JSON_FILE}.JSON")
  endif()
  set(ROUTINEREF_JSON "${DOCUMENT_VISTA_OUTPUT_DIR}/Routine-Ref.json")
  set(PACKAGEDEP_JSON "${DOCUMENT_VISTA_OUTPUT_DIR}/PackageDep.json") # TODO: Where is this file used?
  configure_file(${CMAKE_CURRENT_SOURCE_DIR}/WebPageGenerator.cmake.in ${SCRIPT_OUTPUT_DIR}/WebPageGenerator.cmake @ONLY)
  add_test(WebPageGenerator ${CMAKE_COMMAND} -P ${SCRIPT_OUTPUT_DIR}/WebPageGenerator.cmake)
  set_tests_properties(WebPageGenerator PROPERTIES TIMEOUT 7200)
endif()

if(GENERATE_VIVIAN)
  # 7. Run Cross Reference Builder
  # Generates PackageDependency file used in ViViaN
  set(PACKAGEDEP_JSON "${DOCUMENT_VISTA_OUTPUT_DIR}/pkgdep.json")
  configure_file(${CMAKE_CURRENT_SOURCE_DIR}/GeneratePackageDep.cmake.in ${SCRIPT_OUTPUT_DIR}/GeneratePackageDep.cmake @ONLY)
  add_test(GeneratePackageDep ${CMAKE_COMMAND} -P ${SCRIPT_OUTPUT_DIR}/GeneratePackageDep.cmake)
  set_tests_properties(GeneratePackageDep PROPERTIES TIMEOUT 7200)
endif()