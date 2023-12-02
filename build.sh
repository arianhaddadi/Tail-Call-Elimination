mkdir -p ../submission
cp -r *.py c_files ../submission
cd ../submission
tar -czvf archive.tar.gz --exclude=.DS_Store *.py c_files
rm -rf *.py c_files
mv archive.tar.gz ../source_code.tar.gz
cd ..
rm -rf submission