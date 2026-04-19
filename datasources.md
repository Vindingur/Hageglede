# Plant Data Sources for Hageglede

*Research conducted for Norwegian gardening and plant database project*

---

## Norwegian Plant & Gardening Data Sources

### Official Government APIs

**Artsdatabanken API**  
Norwegian Biodiversity Information Centre providing species habitat associations and distribution data for Norwegian flora.
- Website: https://artsdatabanken.no/
- API available for species data

**GBIF Norway Datasets**  
Multiple plant datasets hosted through GBIF (Global Biodiversity Information Facility):
- Vascular plant inventories
- Historical plant use data
- Red-listed species
- https://www.gbif.org/dataset/search?publishing_country=NO

**Mattilsynet**  
Norwegian Official List of Varieties:
- DUS (Distinctness, Uniformity, Stability) requirements
- VCU (Value for Cultivation and Use) testing data
- https://www.mattilsynet.no/planter-og-dyrking/plantesykdommer-og-skadegjorere/plantevernmidler/rodlisten/

**Geonorge APIs**  
Spatial data access portal through Data.norge.no
- Geospatial datasets for Norway
- https://data.norge.no/

**Landbruksdirektoratet**  
Agricultural resources:
- https://www.landbruksdirektoratet.no/

---

### Research & Specialized Resources

**NIBIO (Norwegian Institute of Bioeconomy Research)**  
- Plant health research
- Climate and environmental modelling
- Klimasmart Jordbruk (Climate Smart Agriculture)
- https://www.nibio.no/

**PhyloNorway Project**  
Genome database for 1,900+ vascular plant taxa in Norway
- Reference genomes for Norwegian flora
- https://www.nhm.uio.no/english/research/projects/phylo-norway/

**Norsk Bruksgenbank**  
Norwegian Genetic Resource Centre:
- Heritage Norwegian vegetable varieties database
- https://www.nordgen.org/en/norskgenbank/

**Nordic-Baltic Plant Breeding Database**  
Climate-resilient plant breeding data for Nordic and Baltic regions
- https://www.nordic-baltic-plant-breeding.org/

**Hagebruk.no**  
Commercial gardening resources:
- 500+ varieties
- https://hagebruk.no/

**Mosevegen.no**  
Norwegian plant nursery and garden resources
- https://mosevegen.no/

---

## Hardiness Zone Data

### European Hardiness Zone Sources

**Note:** No official USDA API exists for Europe. However, several resources provide zone mapping data.

**Plantmaps.com**  
Interactive USDA Hardiness Zone Map for Norway:
- Zone 2a to 10a coverage
- https://www.plantmaps.com/usda-hardiness-zone-map-norway.php

**Gardenia.net**  
European hardiness zones information and plant guides
- https://www.gardenia.net/

**Jelitto Perennial Seeds**  
Hardiness zone reference and growing guides
- https://www.jelitto.com/

**Thrive Garden Life**  
Global zip code/postcode to hardiness zone converter
- https://thrivegardenlife.com/

---

## Offline Botanical Resources

**Kiwix Edible Plant Database**  
Comprehensive offline plant reference:
- 35,000+ species
- Full offline browsing via ZIM format
- https://wiki.kiwix.org/wiki/Content_in_all_languages

**Project NOMAD**  
Docker-based offline plant identification system:
- Comprehensive offline databases
- Similar architectural approach to consider
- https://github.com/Crosstalk-Solutions/project-nomad

**Wikispecies via Kiwix**  
- ~1,000,000 species catalog
- Fully offline capable

---

## Weather Data Sources

**MET Norway's FROST API**  
Comprehensive Norwegian weather data:
- Observations
- Forecasts
- Climate data
- RESTful API
- https://frost.met.no/

---

## Previously Identified Sources

From earlier research:
- **OpenFarm** – Plant database with growing guides
- **MET (Norwegian Meteorological Institute)** – Historical weather and growing seasons
- **Kartverket** – Norwegian mapping authority for spatial data

---

## Recommended Next Steps

1. **Hardiness Zone Mapping**: Use Plantmaps.com + Kartverket spatial data to build postcode → zone mapping
2. **Plant Database**: Evaluate Artsdatabanken API and NIBIO resources for core plant data
3. **Meal Integration**: Scrape or API access to matprat.no (requires separate investigation)
4. **Weather Integration**: MET FROST API for growing season calculations
5. **Offline Capability**: Consider Kiwix integration for remote field use (future phase)

---

*Last updated: [Research Phase]*
