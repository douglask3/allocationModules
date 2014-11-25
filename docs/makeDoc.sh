## Copy reqired hooks
hooksPath="gitinfoHooks/"
hooksDir="../.git/hooks/"

fnames=`ls $hooksPath`
cp `find $hooksPath | tail -n +2` $hooksDir

for i in `ls $hooksPath`
do
    f=$hooksDir$i
    echo $f
    chmod +x $f
done

## Build docs

pdflatex Info.tex
bibtex Info
pdflatex Info.tex
pdflatex Info.tex
