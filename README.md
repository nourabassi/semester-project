# Semester Project Fall 2018 

### About
The repository holds a variety of notebooks which contain a bibliographic analysis of the Papers in the Proceedings of ICLS and CLCS from 2015 to 2018.

The code used to parse and augment the data is eplained in the notebooks contained in the `Parsing Explained` folder. 

The analysis of the data itself is split into the different notebooks as to avoid having to load overly large notebooks, which lead to lagging.

### What each notebook contains:

- Analysis.ipynb :
- Co_citations.ipynb :
- Coauthorship analysis.ipynb: looks at the social network formed by co-athorship and how the community is structured.
- Data exploration - References.ipynb	: look at what information can be extracted from the references of the papers. What papers are most cited, which researchers are most cited. Additonaly frequently referenced conferences and journals are found.
- Data exploration - Universities & Countries .ipynb : looks at the where participants are from and how countries and institutions collaborate.
- Papers - Metadata Analysis.ipynb : look at the metadata which was collected seperatly from the other data which was extracted from the pdf papers. Discusses some issues with the data and looks at participation.

### Rerunning the parsing:
Rerunning the parsing is not necessary unless additional data becomes available. All the data is contained in the `data` folder. Where possible in `csv` format. The data associated to universities is saved in `pickle` format to keep the emails associated to participants hidden from malicious robots.

To rerun the parsing:
1. Make sure you have conda installed. for more information [click here](https://conda.io/docs/user-guide/install/index.html)
2. to get all the dependencied, create an environment using 
```conda env create -f environment.yml```  and activate the environment using: 
```source activate Biblio``` 
3. run ```bash init```
4. rerun Parsing University and Country.ipynb (takes a long time and should be inspected) this can be done from the comand line using ```jupyter nbconvert --execute Parsing\ University\ and\ Country.ipynb```. Should not be rerun often to avoid unnecessary API calls. This is the only part of parsing which requires a working connection to the internet to execute.

### Rerunning the notebooks:

Follow step 1&2 above to set up the environment in which all dependencies are loaded.
