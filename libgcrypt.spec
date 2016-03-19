%define	major 20
%define	libname %mklibname gcrypt %{major}
%define	devname %mklibname gcrypt -d

# disable tests by default, no /dev/random feed, no joy
#(proyvind): conditionally reenabled it with a check for /dev/random first
%bcond_without	check
%bcond_with	uclibc
%bcond_with	crosscompile

Summary:	GNU Cryptographic library
Name:		libgcrypt
Version:	1.6.4
Release:	3
License:	LGPLv2+
Group:		System/Libraries
Url:		http://www.gnupg.org/
Source0:	ftp://ftp.gnupg.org/gcrypt/libgcrypt/%{name}-%{version}.tar.bz2
Patch0:		libgcrypt-1.2.0-libdir.patch
Patch1:		libgcrypt-1.6.2-add-pkgconfig-support.patch 
Patch2:		libgcrypt-1.6.1-fix-a-couple-of-tests.patch
# fix for memory leaks an other errors found by Coverity scan
Patch9:		libgcrypt-1.6.1-leak.patch
# use poll instead of select when gathering randomness
Patch11:	libgcrypt-1.6.1-use-poll.patch
# slight optimalization of mpicoder.c to silence Valgrind (#968288)
Patch13:	libgcrypt-1.6.1-mpicoder-gccopt.patch

BuildRequires:	pth-devel
BuildRequires:	pkgconfig(gpg-error)
%if %{with uclibc}
BuildRequires:	uClibc-devel >= 0.9.33.2-15
BuildRequires:	uclibc-pth-devel
BuildRequires:	uclibc-libgpg-error-devel
%endif

%description
Libgcrypt is a general purpose cryptographic library
based on the code from GNU Privacy Guard.  It provides functions for all
cryptograhic building blocks: symmetric ciphers
(AES,DES,Blowfish,CAST5,Twofish,Arcfour), hash algorithms (MD5,
RIPE-MD160, SHA-1, TIGER-192), MACs (HMAC for all hash algorithms),
public key algorithms (RSA, ElGamal, DSA), large integer functions,
random numbers and a lot of supporting functions.

%package -n	%{libname}
Summary:	GNU Cryptographic library
Group:		System/Libraries

%description -n	%{libname}
Libgcrypt is a general purpose cryptographic library
based on the code from GNU Privacy Guard.  It provides functions for all
cryptograhic building blocks: symmetric ciphers
(AES,DES,Blowfish,CAST5,Twofish,Arcfour), hash algorithms (MD5,
RIPE-MD160, SHA-1, TIGER-192), MACs (HMAC for all hash algorithms),
public key algorithms (RSA, ElGamal, DSA), large integer functions,
random numbers and a lot of supporting functions.

%if %{with uclibc}
%package -n	uclibc-%{libname}
Summary:	GNU Cryptographic library (uClibc build)
Group:		System/Libraries

%description -n	uclibc-%{libname}
Libgcrypt is a general purpose cryptographic library
based on the code from GNU Privacy Guard.  It provides functions for all
cryptograhic building blocks: symmetric ciphers
(AES,DES,Blowfish,CAST5,Twofish,Arcfour), hash algorithms (MD5,
RIPE-MD160, SHA-1, TIGER-192), MACs (HMAC for all hash algorithms),
public key algorithms (RSA, ElGamal, DSA), large integer functions,
random numbers and a lot of supporting functions.

%package -n	uclibc-%{devname}
Summary:	Development files for GNU cryptographic library
Group:		Development/Other
Requires:	uclibc-%{libname} = %{EVRD}
Requires:	%{devname} = %{EVRD}
Provides:	uclibc-%{name}-devel = %{EVRD}
Conflicts:	%{devname} < 1.6.3-2

%description -n	uclibc-%{devname}
This package contains files needed to develop applications using libgcrypt.
%endif

%package -n	%{devname}
Summary:	Development files for GNU cryptographic library
Group:		Development/Other
Requires:	%{libname} = %{version}-%{release}
Provides:	%{name}-devel = %{version}-%{release}

%description -n	%{devname}
This package contains files needed to develop applications using libgcrypt.

%prep
%setup -q
%apply_patches

autoreconf -fiv

%build
%if %{with crosscompile}
ac_cv_sys_symbol_underscore=no
%endif
CONFIGURE_TOP="$PWD"
%if %{with uclibc}
mkdir -p uclibc
pushd uclibc
%uclibc_configure \
	--enable-shared \
	--enable-static \
	--enable-m-guard \
	--disable-amd64-as-feature-detection
%make
popd
%endif

mkdir -p system
pushd system
%configure \
	--enable-shared \
	--enable-static \
%if %{with crosscompile}
	--with-gpg-error-prefix=$SYSROOT/%{_prefix} \
%endif
	--enable-m-guard \
	--disable-amd64-as-feature-detection
%make
popd

%if %{with check}
%check
# (proyvind): some features (ie. amd64-as-feature-detection) breaks with
# uClibc build, so we need to run checks for uClibc build as well..
%if %{with uclibc}
test -c /dev/random && LD_LIBRARY_PATH=$PWD/uclibc/src/.libs make -C uclibc check
%endif

test -c /dev/random && make -C system check
%endif

%install
%if %{with uclibc}
%makeinstall_std -C uclibc
mkdir -p %{buildroot}%{uclibc_root}/%{_lib}
mv %{buildroot}%{uclibc_root}%{_libdir}/libgcrypt.so.%{major}* %{buildroot}%{uclibc_root}/%{_lib}
ln -srf %{buildroot}%{uclibc_root}/%{_lib}/libgcrypt.so.%{major}.*.* %{buildroot}%{uclibc_root}%{_libdir}/libgcrypt.so

rm -r %{buildroot}%{uclibc_root}%{_libdir}/pkgconfig
rm -r %{buildroot}%{uclibc_root}%{_bindir}
%endif

%makeinstall_std -C system
mkdir -p %{buildroot}/%{_lib}
mv %{buildroot}%{_libdir}/libgcrypt.so.%{major}* %{buildroot}/%{_lib}
ln -srf %{buildroot}/%{_lib}/libgcrypt.so.%{major}.*.* %{buildroot}%{_libdir}/libgcrypt.so

%files -n %{libname}
/%{_lib}/libgcrypt.so.%{major}*

%if %{with uclibc}
%files -n uclibc-%{libname}
%{uclibc_root}/%{_lib}/libgcrypt.so.%{major}*

%files -n uclibc-%{devname}
%{uclibc_root}%{_libdir}/libgcrypt.a
%{uclibc_root}%{_libdir}/libgcrypt.so
%endif

%files -n %{devname}
%doc AUTHORS README* NEWS THANKS TODO ChangeLog
%{_bindir}/*
%{_includedir}/gcrypt.h
%{_libdir}/libgcrypt.a
%{_libdir}/libgcrypt.so
%{_libdir}/pkgconfig/libgcrypt.pc
%{_datadir}/aclocal/libgcrypt.m4
%{_mandir}/man1/hmac256.1*
%{_infodir}/gcrypt.info*
