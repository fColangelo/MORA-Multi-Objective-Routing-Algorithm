# Multi-Objective Routing Algorithm (MORA)

This repo contains the code for the paper ....

## OPEN ISSUES:
1. Fault generation and handling

⋅⋅* Aggiunta dei flows "rimossi" alla lista di quelli da instradare (in traffic generator) --> Proposta: ripristiniamo l'attributo dei link che manteneva traccia dei flussi instradati "su" di esso. In questo modo quando un link viene buttato giù è facile ottenere i flussi da reinstradare. Posso occuparmi io facilmente di implementare questa parte. Per il resto della logica ne dovremmo parlare prima insieme.

⋅⋅* Che succede se un pezzo di topologia rimane isolata? Facciamo screening dei flows o implementiamo algoritmo per algoritmo un check? Direi la prima --> al netto di quanto ci siamo già detti, risolto il punto precedente, questo mi sembra abbastanza facile

2. Traffic generator
⋅⋅* Check se i problemi di clock creano problemi di simulazione (MA COME?) --> valutare e ottimizzare il tempo di esecuzione della funzione traffic_generator.generate_flows(). Tale tempo sarà il delta in più tra due periodi di esecuzione successivi.

## TEST:
--> intendi dei pytest? o una cosa quick and dirty?
Fammi qualche esempio per le 3 categorie successive please
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
⋅⋅* Determinare il minimo intervallo che possiamo impostare tra un file e l'altro --> dipende fortemente dal punto 2 della sezione ##OPEN ISSUES

## TODOs:
1. Flow restrictions and trust levels --> vogliamo inserire nuovamente i trust levels? Cosa intendi per flow restrictions ?

## Commenti Marco & Errori codice
1. traffic_generator - line 187 --> manca l'argomento del .remove(): self.old_path_archive.remove()
2. Perchè alla fine di apply_flows() viene chiamata self.topo.update_link_status() ? Questa funzione spegne i link se consumed_bandwidth==0...
   1. Perchè li spegne?
   2. Comunque, per spegnerli è meglio utilizzare topology.switch_off_link(link), perchè aggiorna altre cose oltre a settare lo status = "off"
   3. ...