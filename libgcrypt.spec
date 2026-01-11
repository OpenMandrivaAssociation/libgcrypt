%define major 20
%define oldlibname %mklibname gcrypt 20
%define libname %mklibname gcrypt
%define devname %mklibname gcrypt -d
%define staticname %mklibname gcrypt -d -s

%global optflags %{optflags} -O3 -falign-functions=32 -fno-math-errno -fno-trapping-math
%global build_ldflags %{build_ldflags} -Wl,--undefined-version

# libgcrypt is used by gnutls and libxslt, both of which in turn
# are used by wine.
%ifarch %{x86_64}
%bcond_without compat32
%else
%bcond_with compat32
%endif
%if %{with compat32}
%define oldlib32name libgcrypt%{major}
%define lib32name libgcrypt
%define dev32name libgcrypt-devel
%define static32name libgcrypt-static-devel
%endif

# (tpg) enable PGO build
%if %{cross_compiling}
%bcond_with pgo
%bcond_with check
%else
%bcond_without pgo
%bcond_without check
%endif

Summary:	GNU Cryptographic library
Name:		libgcrypt
Version:	1.11.2
Release:	1
License:	LGPLv2+
Group:		System/Libraries
Url:		https://www.gnupg.org/
Source0:	https://www.gnupg.org/ftp/gcrypt/libgcrypt/%{name}-%{version}.tar.bz2
# CMake file that used to be shipped with libxslt, but really belongs with libgcrypt
Source1:	https://gitlab.gnome.org/GNOME/libxslt/-/raw/master/FindGcrypt.cmake
BuildRequires:	autoconf
BuildRequires:	automake
BuildRequires:	libtool-base
BuildRequires:	slibtool
BuildRequires:	make
BuildRequires:	pkgconfig(gpg-error)
%if %{with compat32}
BuildRequires:	devel(libgpg-error)
BuildRequires:	libc6
%rename %{oldlib32name}
%endif

%patchlist
libgcrypt-1.2.0-libdir.patch
libgcrypt-1.8.5-detect-m32.patch
libgcrypt-1.9.1-i686-compile.patch
# (tpg) try to fix noexecstack with clang. This is very important to have noexecstack
libgcrypt-1.8.3-enable-noexecstack.patch
# (tpg) fix build with LLVM/clang
libgcrypt-1.8.3-fix-clang-optimization.patch
libgcrypt-1.11.2-workaround-__thread-check.patch

%description
Libgcrypt is a general purpose cryptographic library
based on the code from GNU Privacy Guard.  It provides functions for all
cryptograhic building blocks: symmetric ciphers
(AES,DES,Blowfish,CAST5,Twofish,Arcfour), hash algorithms (MD5,
RIPE-MD160, SHA-1, TIGER-192), MACs (HMAC for all hash algorithms),
public key algorithms (RSA, ElGamal, DSA), large integer functions,
random numbers and a lot of supporting functions.

%package -n %{libname}
Summary:	GNU Cryptographic library
Group:		System/Libraries
# renamed after 5.0
%rename %{oldlibname}

%description -n %{libname}
Libgcrypt is a general purpose cryptographic library
based on the code from GNU Privacy Guard.  It provides functions for all
cryptograhic building blocks: symmetric ciphers
(AES,DES,Blowfish,CAST5,Twofish,Arcfour), hash algorithms (MD5,
RIPE-MD160, SHA-1, TIGER-192), MACs (HMAC for all hash algorithms),
public key algorithms (RSA, ElGamal, DSA), large integer functions,
random numbers and a lot of supporting functions.

%package -n %{devname}
Summary:	Development files for GNU cryptographic library
Group:		Development/Other
Requires:	%{libname} = %{EVRD}
Requires:	pkgconfig(gpg-error)

%description -n %{devname}
This package contains files needed to develop applications using libgcrypt.

%package -n %{staticname}
Summary:	Static library files for GNU cryptographic library
Group:		Development/Other
Requires:	%{devname} = %{EVRD}

%description -n %{staticname}
This package contains files needed to link applications using libgcrypt
statically.

%if %{with compat32}
%if "%{lib32name}" != "%{name}"
%package -n %{lib32name}
Summary:	GNU Cryptographic library (32-bit)
Group:		System/Libraries
# renamed after 5.0
%rename %{oldlib32name}

%description -n %{lib32name}
Libgcrypt is a general purpose cryptographic library
based on the code from GNU Privacy Guard.  It provides functions for all
cryptograhic building blocks: symmetric ciphers
(AES,DES,Blowfish,CAST5,Twofish,Arcfour), hash algorithms (MD5,
RIPE-MD160, SHA-1, TIGER-192), MACs (HMAC for all hash algorithms),
public key algorithms (RSA, ElGamal, DSA), large integer functions,
random numbers and a lot of supporting functions.
%endif

%package -n %{dev32name}
Summary:	Development files for GNU cryptographic library (32-bit)
Group:		Development/Other
Requires:	%{lib32name} = %{EVRD}
Requires:	%{devname} = %{EVRD}
Requires:	devel(libgpg-error)

%description -n %{dev32name}
This package contains files needed to develop applications using libgcrypt.

%package -n %{static32name}
Summary:	Static library files for GNU cryptographic library (32-bit)
Group:		Development/Other
Requires:	%{dev32name} = %{EVRD}

%description -n %{static32name}
This package contains files needed to link applications using libgcrypt
statically.
%endif

%prep
%autosetup -p1
autoreconf -fiv

%build
if as --help | grep -q execstack; then
  # the object files do not require an executable stack
  export CCAS="%{__cc} -c -Wa,--noexecstack"
fi

export CONFIGURE_TOP="$(pwd)"
%if %{with compat32}
mkdir build32
cd build32
%configure32 \
	--enable-shared \
	--enable-static \
	--disable-O-flag-munging \
	--enable-pubkey-ciphers='dsa elgamal rsa ecc' \
	--disable-hmac-binary-check \
	--disable-large-data-tests \
	--enable-noexecstack \
%ifnarch %{x86_64}
	--disable-sse41-support \
%endif
	--enable-m-guard \
	--disable-amd64-as-feature-detection
%make_build
cd ..
%endif

mkdir build
cd build
%if %{with pgo}
export LD_LIBRARY_PATH="$(pwd)"

CFLAGS="%{optflags} -flto -fprofile-generate -mllvm -vp-counters-per-site=32" \
CXXFLAGS="%{optflags} -flto -fprofile-generate" \
LDFLAGS="%{build_ldflags} -flto -fprofile-generate" \
%configure \
	--enable-shared \
	--enable-static \
	--disable-O-flag-munging \
	--enable-pubkey-ciphers='dsa elgamal rsa ecc' \
	--disable-hmac-binary-check \
	--disable-large-data-tests \
	--enable-noexecstack \
%ifnarch %{x86_64}
	--disable-sse41-support \
%endif
	--enable-m-guard \
	--disable-amd64-as-feature-detection

[ -e libtool ] && sed -i -e '/^sys_lib_dlsearch_path_spec/s,/lib /usr/lib,/usr/lib /lib64 /usr/lib64 /lib,g' libtool
%make_build

test -c /dev/urandom && make check

unset LD_LIBRARY_PATH
llvm-profdata merge --output=%{name}-llvm.profdata $(find . -name "*.profraw" -type f)
PROFDATA="$(realpath %{name}-llvm.profdata)"
rm -f *.profraw

make clean

CFLAGS="%{optflags} -flto -fprofile-use=$PROFDATA" \
CXXFLAGS="%{optflags} -flto -fprofile-use=$PROFDATA" \
LDFLAGS="%{build_ldflags} -flto -fprofile-use=$PROFDATA" \
%endif
%configure \
	--enable-shared \
	--enable-static \
	--disable-O-flag-munging \
	--enable-pubkey-ciphers='dsa elgamal rsa ecc' \
	--disable-hmac-binary-check \
	--disable-large-data-tests \
	--enable-noexecstack \
%ifnarch %{x86_64}
	--disable-sse41-support \
%endif
	--enable-m-guard \
	--disable-amd64-as-feature-detection

[ -e libtool ] && sed -i -e '/^sys_lib_dlsearch_path_spec/s,/lib /usr/lib,/usr/lib /lib64 /usr/lib64 /lib,g' libtool
%make_build

%if %{with check}
%ifnarch aarch64
%check
%if %{with compat32}
test -c /dev/urandom && make -C build32 check
%endif
test -c /dev/urandom && make -C build check
%endif
%endif

%install
%if %{with compat32}
%make_install -C build32
%endif

%make_install -C build

mkdir -p %{buildroot}%{_libdir}/cmake/%{name}
cp %{S:1} %{buildroot}%{_libdir}/cmake/%{name}/

%files -n %{libname}
%{_libdir}/libgcrypt.so.%{major}*

%files -n %{devname}
%doc AUTHORS README* NEWS THANKS TODO ChangeLog
%{_bindir}/*
%{_includedir}/gcrypt.h
%{_libdir}/libgcrypt.so
%{_libdir}/pkgconfig/libgcrypt.pc
%{_libdir}/cmake/%{name}
%{_datadir}/aclocal/libgcrypt.m4
%doc %{_mandir}/man1/hmac256.1*
%doc %{_infodir}/gcrypt.info*

%files -n %{staticname}
%{_libdir}/libgcrypt.a

%if %{with compat32}
%files -n %{lib32name}
%{_prefix}/lib/libgcrypt.so.%{major}*

%files -n %{dev32name}
%{_prefix}/lib/libgcrypt.so
%{_prefix}/lib/pkgconfig/libgcrypt.pc

%files -n %{static32name}
%{_prefix}/lib/libgcrypt.a
%endif
