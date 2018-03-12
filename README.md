# A convenient interface to dockerised command line tools.

## Basic Install
```bash
$ git clone https://github.com/Karhide/DKR
$ cd dkr
$ python setup.py install
```
## Example usage
### Search
```bash
$ dkr-search minimap2

    Name      Tag          URL                                         Registry
--  --------  -----------  ------------------------------------------  ---------------------
 1  minimap2  2.9--1       quay.io/biocontainers/minimap2:2.9--1       quay.io/biocontainers
 2  minimap2  2.8--1       quay.io/biocontainers/minimap2:2.8--1       quay.io/biocontainers
 3  minimap2  2.8--0       quay.io/biocontainers/minimap2:2.8--0       quay.io/biocontainers
 4  minimap2  2.7--0       quay.io/biocontainers/minimap2:2.7--0       quay.io/biocontainers
 5  minimap2  2.6.1--0     quay.io/biocontainers/minimap2:2.6.1--0     quay.io/biocontainers
 6  minimap2  2.6--0       quay.io/biocontainers/minimap2:2.6--0       quay.io/biocontainers
 7  minimap2  2.5--0       quay.io/biocontainers/minimap2:2.5--0       quay.io/biocontainers
 8  minimap2  2.4--0       quay.io/biocontainers/minimap2:2.4--0       quay.io/biocontainers
 9  minimap2  2.3--0       quay.io/biocontainers/minimap2:2.3--0       quay.io/biocontainers
10  minimap2  2.1.r311--0  quay.io/biocontainers/minimap2:2.1.r311--0  quay.io/biocontainers
11  minimap2  2.1.1--0     quay.io/biocontainers/minimap2:2.1.1--0     quay.io/biocontainers
12  minimap2  2.0.r191--0  quay.io/biocontainers/minimap2:2.0.r191--0  quay.io/biocontainers

Total 12
```
### Add manually
```bash
$ dkr-add -i quay.io/biocontainers/bwa:0.7.17--pl5.22.0_2 -e bwa
```
### Add from search
```bash
$ dkr-search minimap2 1 | dkr-add
```
### List
```bash
$ dkr-list

  #  Entrypoint    Images                                        Local
---  ------------  --------------------------------------------  -------
  1  bwa           quay.io/biocontainers/bwa:0.7.17--pl5.22.0_2  True
  2  minimap2      quay.io/biocontainers/minimap2:2.9--1         False

Total 2
```
### Run
```bash
$ dkr minimap2 -x map-ont -t 16 -a \
    GCA_000001405.15_GRCh38_genomic.fna.minimap2.idx reads.fastq > read_mapped.sam
```
### Piping
```bash
$ dkr minimap2 -x map-ont -t 16 -a \
    GCA_000001405.15_GRCh38_genomic.fna.minimap2.idx reads.fastq \
    | dkr samtools view -Sbh - > read_mapped.bam
```
### Pull manually
```bash
$ dkr-list 2 | dkr-pull

2.9--1: Pulling from biocontainers/minimap2
a3ed95caeb02: Already exists
b0dc45cd432d: Already exists
9466b3513669: Already exists
ddd482ea7b54: Already exists
4d69f833b9d8: Already exists
e7c454e5167d: Already exists
e38092b005c0: Already exists
f879b42dfe2b: Already exists
c56cf103d24d: Pull complete
Digest: sha256:a5ffd15959aff0e491f88561c1c632db1048c23b3257d7f8bc32bf6c7a044b40
Status: Downloaded newer image for quay.io/biocontainers/minimap2:2.9--1
```
### Remove
```bash
$ dkr-list 1 | dkr-remove
```
## Authors:
https://github.com/coelias
https://github.com/philres
https://github.com/Karhide
