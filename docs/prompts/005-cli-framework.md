\# Mission Control CLI Framework

Version 1.0



Read the existing Mission Control CLI.



The CLI is functional.



Do NOT rewrite functionality.



Instead perform an architectural refactor.



=========================================================

OBJECTIVE

=========================================================



Transform Mission Control into a production-quality CLI framework.



The CLI must become modular, maintainable and extensible.



The entry point



scripts/mc.ps1



must contain ONLY



Argument parsing



Command dispatch



Loading libraries



Error handling



Everything else belongs in modules.



Maximum size



200 lines



=========================================================

DIRECTORY STRUCTURE

=========================================================



Create



scripts/



config/



commands/



lib/



templates/



logs/



=========================================================

COMMAND ARCHITECTURE

=========================================================



Every command must live in



scripts/commands



Examples



Help.ps1



Doctor.ps1



Status.ps1



Version.ps1



Docker.ps1



Git.ps1



Sprint.ps1



Build.ps1



Test.ps1



Lint.ps1



Clean.ps1



Dev.ps1



=========================================================

LIBRARIES

=========================================================



Create reusable libraries.



Bootstrap.ps1



Output.ps1



Logger.ps1



Helpers.ps1



Validation.ps1



Docker.ps1



Git.ps1



Http.ps1



Doctor.ps1



Version.ps1



Project.ps1



=========================================================

GLOBAL PARAMETERS

=========================================================



Every command automatically supports



\--help



\--verbose



\--quiet



\--debug



\--output console



\--output json



\--output json-pretty



\--no-color



\--log



\--config



=========================================================

OUTPUT ENGINE

=========================================================



Create



Output.ps1



Commands return PowerShell objects.



Rendering occurs ONLY in Output.ps1.



Supported



Console



JSON



Pretty JSON



Future



Markdown



HTML



Do not duplicate rendering logic.



=========================================================

LOGGER

=========================================================



Logger.ps1



Supports



INFO



WARN



ERROR



DEBUG



SUCCESS



Timestamped logging



Log file



Console



=========================================================

COMMAND PATTERN

=========================================================



Every command follows



Validate



↓



Execute



↓



Return Object



↓



Output Engine



=========================================================

HELP SYSTEM

=========================================================



mc help



mc doctor --help



mc docker --help



Generated automatically.



=========================================================

CONFIGURATION

=========================================================



Store CLI configuration inside



scripts/config



Support future user configuration.



=========================================================

TEMPLATES

=========================================================



Move sprint templates into



scripts/templates



=========================================================

BACKWARD COMPATIBILITY

=========================================================



Existing commands MUST continue working.



doctor



status



version



docker



git



init



=========================================================

QUALITY

=========================================================



Use CmdletBinding.



PowerShell 7+



Comment-based help



Advanced Functions



No duplicated code



No global variables



=========================================================

ACCEPTANCE

=========================================================



mc help



mc doctor



mc doctor --output json



mc version



mc docker up



mc docker down



mc git status



must all continue working.



Output engine shared.



Logger shared.



Entry point under 200 lines.



Summarize every modified file.

