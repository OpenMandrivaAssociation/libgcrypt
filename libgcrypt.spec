%define	major	11
%define	libname	%mklibname gcrypt %{major}
%define	devname	%mklibname gcrypt -d

# disable tests by default, no /dev/random feed, no joy
%bcond_with	check
%bcond_without	uclibc

Summary:	GNU Cryptographic library
Name:		libgcrypt
Version:	1.5.0
Release:	4
License:	LGPLv2+
Group:		System/Libraries
Url:		http://www.gnupg.org/
# don't convert to bzip2, since we ship archive signature
Source0:	ftp://ftp.gnupg.org/gcrypt/libgcrypt/%{name}-%{version}.tar.bz2
Source1:	ftp://ftp.gnupg.org/gcrypt/libgcrypt/%{name}-%{version}.tar.bz2.sig
Patch1:		libgcrypt-1.2.0-libdir.patch
Patch2:		libgcrypt-1.5.0-gcry_mpi_print-volatile-len-variable.patch
Patch3:		libgcrypt-1.5.0-add-pkgconfig-support.patch 
BuildRequires:	pkgconfig(gpg-error)
BuildRequires:	pth-devel
%if %{with uclibc}
BuildRequires:	uClibc-devel >= 0.9.33.2-15
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

%package -n	%{devname}
Summary:	Development files for GNU cryptographic library
Group:		Development/Other
Requires:	%{libname} = %{version}-%{release}
%if %{with uclibc}
Requires:	uclibc-%{libname} = %{version}-%{release}
%endif
Provides:	%{name}-devel = %{version}-%{release}
Obsoletes:	%mklibname -d gcrypt 11

%description -n	%{devname}
Libgcrypt is a general purpose cryptographic library
based on the code from GNU Privacy Guard.
This package contains files needed to develop
applications using libgcrypt. ( For example Ägypten project )

%prep
%setup -q
%patch1 -p1 -b .libdir~
%patch2 -p1 -b .volatile~
%patch3 -p1 -b .pkgconf~ 
autoreconf -f

%build
CONFIGURE_TOP="$PWD"
%if %{with uclibc}
mkdir -p uclibc
pushd uclibc
%uclibc_configure \
		--enable-shared \
		--enable-static \
		--enable-m-guard
%make
popd
%endif

mkdir -p system
pushd system
%configure2_5x	--enable-shared \
		--enable-static \
		--enable-m-guard
%make
popd

%if %{with check}
%check
make -C system check
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
%doc AUTHORS README NEWS THANKS TODO
/%{_lib}/libgcrypt.so.%{major}*

%if %{with uclibc}
%files -n uclibc-%{libname}
%{uclibc_root}/%{_lib}/libgcrypt.so.%{major}*
%endif

%files -n %{devname}
%doc ChangeLog README.*
%{_bindir}/*
%{_includedir}/gcrypt.h
%{_includedir}/gcrypt-module.h
%{_libdir}/libgcrypt.a
%{_libdir}/libgcrypt.so
%if %{with uclibc}
%{uclibc_root}%{_libdir}/libgcrypt.a
%{uclibc_root}%{_libdir}/libgcrypt.so
%endif
%{_libdir}/pkgconfig/libgcrypt.pc
%{_datadir}/aclocal/libgcrypt.m4
%{_infodir}/gcrypt.info*
