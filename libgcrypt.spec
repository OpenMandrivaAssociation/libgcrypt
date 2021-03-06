%define major 20
%define libname %mklibname gcrypt %{major}
%define devname %mklibname gcrypt -d
%define staticname %mklibname gcrypt -d -s

# Workaround for gcc -m32. No harm done because we re-add -flto
# for the 64bit build.
%global _disable_lto 1

%global optflags %{optflags} -O3 -falign-functions=32 -fno-math-errno -fno-trapping-math

# disable tests by default, no /dev/random feed, no joy
#(proyvind): conditionally reenabled it with a check for /dev/random first
%bcond_without check
%bcond_with crosscompile

# libgcrypt is used by gnutls and libxslt, both of which in turn
# are used by wine.
%ifarch %{x86_64}
%bcond_without compat32
%else
%bcond_with compat32
%endif
%if %{with compat32}
%define lib32name libgcrypt%{major}
%define dev32name libgcrypt-devel
%define static32name libgcrypt-static-devel
%endif

# (tpg) enable PGO build
%ifnarch riscv64
%bcond_without pgo
%else
%bcond_with pgo
%endif

Summary:	GNU Cryptographic library
Name:		libgcrypt
Version:	1.9.3
Release:	1
License:	LGPLv2+
Group:		System/Libraries
Url:		http://www.gnupg.org/
Source0:	https://www.gnupg.org/ftp/gcrypt/libgcrypt/%{name}-%{version}.tar.bz2
Patch0:		libgcrypt-1.2.0-libdir.patch
Patch1:		libgcrypt-1.8.5-detect-m32.patch
#Patch2:		libgcrypt-1.6.1-fix-a-couple-of-tests.patch
# (tpg) Patches from Fedora
# make FIPS hmac compatible with fipscheck - non upstreamable
# update on soname bump
Patch3:		https://src.fedoraproject.org/cgit/rpms/libgcrypt.git/plain/libgcrypt-1.8.5-use-fipscheck.patch
Patch5:		libgcrypt-1.9.1-i686-compile.patch
# use poll instead of select when gathering randomness
Patch11:	https://src.fedoraproject.org/cgit/rpms/libgcrypt.git/plain/libgcrypt-1.8.4-use-poll.patch
# (tpg) try to fix noexecstack with clang. This is very important to have noexecstack
Patch13:	libgcrypt-1.8.3-enable-noexecstack.patch
# (tpg) fix build with LLVM/clang
Patch14:	libgcrypt-1.8.3-fix-clang-optimization.patch
BuildRequires:	pkgconfig(gpg-error)
%if %{with compat32}
BuildRequires:	devel(libgpg-error)
%endif

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
%package -n %{lib32name}
Summary:	GNU Cryptographic library (32-bit)
Group:		System/Libraries

%description -n %{lib32name}
Libgcrypt is a general purpose cryptographic library
based on the code from GNU Privacy Guard.  It provides functions for all
cryptograhic building blocks: symmetric ciphers
(AES,DES,Blowfish,CAST5,Twofish,Arcfour), hash algorithms (MD5,
RIPE-MD160, SHA-1, TIGER-192), MACs (HMAC for all hash algorithms),
public key algorithms (RSA, ElGamal, DSA), large integer functions,
random numbers and a lot of supporting functions.

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
%if %{with crosscompile}
ac_cv_sys_symbol_underscore=no
%endif
# (tpg) try to fix
# fips.c:596: error: undefined reference to 'dladdr'
%global ldflags %ldflags -ldl

if as --help | grep -q execstack; then
  # the object files do not require an executable stack
  export CCAS="%{__cc} -c -Wa,--noexecstack"
fi

export CONFIGURE_TOP="`pwd`"
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
%if %{with crosscompile}
	--with-gpg-error-prefix=$SYSROOT/%{_prefix} \
%endif
	--enable-m-guard \
	--disable-amd64-as-feature-detection
%make_build
cd ..
%endif

mkdir build
cd build
%if %{with pgo}
export LLVM_PROFILE_FILE=%{name}-%p.profile.d
export LD_LIBRARY_PATH="$(pwd)"
CFLAGS="%{optflags} -fprofile-instr-generate -flto" \
CXXFLAGS="%{optflags} -fprofile-instr-generate -flto" \
FFLAGS="$CFLAGS" \
FCFLAGS="$CFLAGS" \
LDFLAGS="%{ldflags} -fprofile-instr-generate -flto" \
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
%if %{with crosscompile}
	--with-gpg-error-prefix=$SYSROOT/%{_prefix} \
%endif
	--enable-m-guard \
	--disable-amd64-as-feature-detection

sed -i -e '/^sys_lib_dlsearch_path_spec/s,/lib /usr/lib,/usr/lib /lib64 /usr/lib64 /lib,g' libtool
%make_build

test -c /dev/urandom && make check

unset LD_LIBRARY_PATH
unset LLVM_PROFILE_FILE
llvm-profdata merge --output=%{name}.profile *.profile.d

make clean

CFLAGS="%{optflags} -fprofile-instr-use=$(realpath %{name}.profile) -flto" \
CXXFLAGS="%{optflags} -fprofile-instr-use=$(realpath %{name}.profile) -flto" \
LDFLAGS="%{ldflags} -fprofile-instr-use=$(realpath %{name}.profile) -flto" \
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
%if %{with crosscompile}
	--with-gpg-error-prefix=$SYSROOT/%{_prefix} \
%endif
	--enable-m-guard \
	--disable-amd64-as-feature-detection

sed -i -e '/^sys_lib_dlsearch_path_spec/s,/lib /usr/lib,/usr/lib /lib64 /usr/lib64 /lib,g' libtool
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
mkdir -p %{buildroot}/%{_lib}
mv %{buildroot}%{_libdir}/libgcrypt.so.%{major}* %{buildroot}/%{_lib}
ln -srf %{buildroot}/%{_lib}/libgcrypt.so.%{major}.*.* %{buildroot}%{_libdir}/libgcrypt.so

%files -n %{libname}
/%{_lib}/libgcrypt.so.%{major}*

%files -n %{devname}
%doc AUTHORS README* NEWS THANKS TODO ChangeLog
%{_bindir}/*
%{_includedir}/gcrypt.h
%{_libdir}/libgcrypt.so
%{_libdir}/pkgconfig/libgcrypt.pc
%{_datadir}/aclocal/libgcrypt.m4
%{_mandir}/man1/hmac256.1*
%{_infodir}/gcrypt.info*

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
