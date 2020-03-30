# Multi-Objective Routing Algorithm (MORA)

This repo contains the code for the paper ....

## OPEN ISSUES:
1. Fault generation and handling
⋅⋅* Aggiunta dei flows "rimossi" alla lista di quelli da instradare (in traffic generator)
⋅⋅* Che succede se un pezzo di topologia rimane isolata? Facciamo screening dei flows o implementiamo algoritmo per algoritmo un check? Direi la prima
2. Traffic generator
⋅⋅* Check se i problemi di clock creano problemi di simulazione (MA COME?)

## TEST:
1. Basic functioning
⋅⋅* MORA
⋅⋅* EAR
⋅⋅* HOP
⋅⋅* D basic
2. Functioning with faults
⋅⋅* MORA
⋅⋅* EAR
⋅⋅* HOP
⋅⋅* D basic
3. Functioning with part of network unreachable
⋅⋅* MORA
⋅⋅* EAR
⋅⋅* HOP
⋅⋅* D basic
4. Traffic generator
⋅⋅* Determinare il minimo intervallo che possiamo impostare tra un file e l'altro

## TODOs:
1. Flow restrictions and trust levels
