cp cmake/warp-rnnt-cmakelist.txt warp-transducer/CMakeLists.txt

cd warp-transducer

mkdir build
cd build

CC=gcc-4.8 CXX=g++-4.8 cmake ..
make
cd ../tensorflow_binding

python setup.py install
cd ../../
