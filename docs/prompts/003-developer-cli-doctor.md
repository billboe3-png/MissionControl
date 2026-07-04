\# Mission Control Developer CLI

\## Sprint 1C - Doctor Command



Read the existing scripts/mc.ps1 implementation.



Extend the existing CLI.



Do NOT rewrite it.



Maintain compatibility with all existing commands.



\--------------------------------------------------

Implement



mc doctor

\--------------------------------------------------



The doctor command must verify:



Environment



✓ PowerShell Version



✓ Git Installed



✓ Git Version



✓ Docker Installed



✓ Docker Running



✓ Docker Compose



✓ Python Installed



✓ Python Version



✓ Node Installed



✓ npm Installed



✓ GitHub Repository



✓ Current Branch



✓ Working Tree Clean



\--------------------------------------------------

If Docker is running



Check



Mission Control Backend



Mission Control Frontend



Mission Control PostgreSQL



Mission Control Redis



Mission Control Nginx



Display



Healthy



Starting



Stopped



Missing



\--------------------------------------------------

If Backend is running



Check



GET /health



GET /ready



GET /version



Display HTTP status.



\--------------------------------------------------

Output



Produce a coloured report.



Green



Yellow



Red



Display



Overall Status



READY



WARNING



FAILED



\--------------------------------------------------

Architecture



Create



scripts/lib/Doctor.ps1



Keep



mc.ps1



small.



Use helper functions.



No duplicated code.



\--------------------------------------------------

Update



help



to include



doctor



\--------------------------------------------------

Do not modify application functionality.



Only extend the developer CLI.

