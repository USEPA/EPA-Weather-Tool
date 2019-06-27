#Filename:        ErrorHandler.py
#Date:            5/25/2017
#Project:         EPA Weather Tool v1.0
#Prepared for:    US EPA Office of Research and Development
#                 National Homeland Security Research Center
#                 Decontamination and Consequences Management Division
#EPA Manager:     Timothy Boe
#Prepared by:     Tetra Tech, Inc. Lafayette, CA
#=======================================================================

# Custom error handling
class Error(Exception):
     def __init__(self, value):
         self.value = value
     def __str__(self):
         return repr(self.value)