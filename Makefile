#!/usr/bin/make -f

clean:
	touch debian
	rm -rf debian

build-deb:
	touch debian
	rm -r debian
	mkdir debian
	cp -pR deb-src/* debian/
	chmod -R 0755 debian/
	dpkg-buildpackage -b -uc -us
