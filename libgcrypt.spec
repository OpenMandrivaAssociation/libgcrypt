%define major 20
%define libname %mklibname gcrypt %{major}
%define devname %mklibname gcrypt -d

%global optflags %{optflags} -O3 -falign-functions=32 -fno-math-errno -fno-trapping-math

# disable tests by default, no /dev/random feed, no joy
#(proyvind): conditionally reenabled it with a check for /dev/random first
%bcond_without check
%bcond_with crosscompile

# (tpg) enable PGO build
%ifnarch riscv64
%bcond_without pgo
%else
%bcond_with pgo
%endif

Summary:	GNU Cryptographic library
Name:		libgcrypt
Version:	1.8.4
Release:	4
License:	LGPLv2+
Group:		System/Libraries
Url:		http://www.gnupg.org/
Source0:	ftp://ftp.gnupg.org/gcrypt/libgcrypt/%{name}-%{version}.tar.bz2
Patch0:		libgcrypt-1.2.0-libdir.patch
Patch1:		libgcrypt-1.6.2-add-pkgconfig-support.patch
Patch2:		libgcrypt-1.6.1-fix-a-couple-of-tests.patch
# (tpg) Patches from Fedora
# make FIPS hmac compatible with fipscheck - non upstreamable
# update on soname bump
Patch3:		libgcrypt-1.6.2-use-fipscheck.patch
# fix tests in the FIPS mode, allow CAVS testing of DSA keygen
Patch4:		libgcrypt-1.8.0-tests.patch
# use poll instead of select when gathering randomness
Patch11:	https://src.fedoraproject.org/cgit/rpms/libgcrypt.git/plain/libgcrypt-1.8.0-use-poll.patch
# (tpg) try to fix noexecstack with clang. This is very important to have noexecstack
Patch13:	libgcrypt-1.8.3-enable-noexecstack.patch
# (tpg) fix build with LLVM/clang
Patch14:	libgcrypt-1.8.3-fix-clang-optimization.patch
BuildRequires:	pkgconfig(gpg-error)
%ifarch %{arm}
BuildRequires:	gcc
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
Provides:	%{name}-devel = %{EVRD}
Requires:	pkgconfig(gpg-error)

%description -n %{devname}
This package contains files needed to develop applications using libgcrypt.

%prep
%autosetup -p1
autoreconf -fiv

%build
%ifarch %{arm}
export CC=gcc
export CXX=g++
%endif
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

%if %{with pgo}
export LLVM_PROFILE_FILE=%{name}-%p.profile.d
export LD_LIBRARY_PATH="$(pwd)"
CFLAGS="%{optflags} -fprofile-instr-generate" \
CXXFLAGS="%{optflags} -fprofile-instr-generate" \
FFLAGS="$CFLAGS" \
FCFLAGS="$CFLAGS" \
LDFLAGS="%{ldflags} -fprofile-instr-generate" \
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

CFLAGS="%{optflags} -fprofile-instr-use=$(realpath %{name}.profile)" \
CXXFLAGS="%{optflags} -fprofile-instr-use=$(realpath %{name}.profile)" \
LDFLAGS="%{ldflags} -fprofile-instr-use=$(realpath %{name}.profile)" \
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
test -c /dev/urandom && make check
%endif
%endif

%install
%make_install
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
