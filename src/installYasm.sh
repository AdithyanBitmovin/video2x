# yasm
wget http://www.tortall.net/projects/yasm/releases/yasm-1.3.0.tar.gz
tar -xvf yasm-1.3.0.tar.gz
rm yasm-1.3.0.tar.gzs
cd yasm-1.3.0/
./configure
sed -i 's#) ytasm.*#)#' Makefile.in
./configure --prefix=/usr
make -j ${CPUS}
sudo make -j${CPUS} install
cd ../
