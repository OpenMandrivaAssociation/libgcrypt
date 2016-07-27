%define	major 20
%define	libname %mklibname gcrypt %{major}
%define	devname %mklibname gcrypt -d

# disable tests by default, no /dev/random feed, no joy
#(proyvind): conditionally reenabled it with a check for /dev/random first
%bcond_without	check
%bcond_with	crosscompile

Summary:	GNU Cryptographic library
Name:		libgcrypt
Version:	1.7.2
Release:	1
License:	LGPLv2+
Group:		System/Libraries
Url:		http://www.gnupg.org/
Source0:	ftp://ftp.gnupg.org/gcrypt/libgcrypt/%{name}-%{version}.tar.bz2
Patch0:		libgcrypt-1.2.0-libdir.patch
Patch1:		libgcrypt-1.6.2-add-pkgconfig-support.patch
Patch2:		libgcrypt-1.6.1-fix-a-couple-of-tests.patch
#Patch3:		libgcrypt-1.7.2-fix-noexec-stack-with-clang.patch
# (tpg) Patches from Fedora
# use poll instead of select when gathering randomness
Patch11:	libgcrypt-1.6.1-use-poll.patch

BuildRequires:	pth-devel
BuildRequires:	pkgconfig(gpg-error)

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
# (tpg) fix missing noexecstack
export CC=gcc
export CXX=g++

%if %{with crosscompile}
ac_cv_sys_symbol_underscore=no
%endif

%configure \
	--enable-shared \
	--enable-static \
%if %{with crosscompile}
	--with-gpg-error-prefix=$SYSROOT/%{_prefix} \
%endif
	--enable-m-guard \
	--disable-amd64-as-feature-detection
%make

%if %{with check}
%ifnarch %{ix86}
%check
test -c /dev/random && make check
%endif
%endif

%install
%makeinstall_std
mkdir -p %{buildroot}/%{_lib}
mv %{buildroot}%{_libdir}/libgcrypt.so.%{major}* %{buildroot}/%{_lib}
ln -srf %{buildroot}/%{_lib}/libgcrypt.so.%{major}.*.* %{buildroot}%{_libdir}/libgcrypt.so

%files -n %{libname}
/%{_lib}/libgcrypt.so.%{major}*

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
