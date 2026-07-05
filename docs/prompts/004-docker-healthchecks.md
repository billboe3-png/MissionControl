Mission Control Sprint 1D

Docker Health Checks



Objective



Implement proper Docker HEALTHCHECK support so every service reports a healthy status.



Current Status



Backend

✓ Healthy



PostgreSQL

✓ Healthy



Redis

✓ Healthy



Frontend

No Docker health check



Nginx

No Docker health check



Tasks



1\.



Frontend



Add a HEALTHCHECK to the frontend Dockerfile.



The health check must verify that the web server responds with HTTP 200.



2\.



Nginx



Add a /health endpoint.



Example



location /health {

&#x20;   access\_log off;

&#x20;   return 200 "OK";

}



Configure Docker Compose to use this endpoint as the nginx health check.



3\.



docker-compose.yml



Add healthcheck definitions for



frontend



nginx



using sensible intervals, retries and timeouts.



4\.



Doctor CLI



Update doctor so that:



If Docker reports



healthy



display



Healthy



If Docker reports



starting



display



Starting



If Docker has no health check configured



display



No Health Check



instead of



Starting



5\.



Acceptance Criteria



docker compose up --build



starts successfully.



docker compose ps



shows



Backend (healthy)



Postgres (healthy)



Redis (healthy)



Frontend (healthy)



Nginx (healthy)



Mission Control Doctor



reports



Healthy



for every running service.



Do not modify application functionality.



Only implement Docker health reporting.

