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
Version:	1.11.0
Release:	2
License:	LGPLv2+
Group:		System/Libraries
Url:		http://www.gnupg.org/
Source0:	https://www.gnupg.org/ftp/gcrypt/libgcrypt/%{name}-%{version}.tar.bz2
Patch0:		libgcrypt-1.2.0-libdir.patch
Patch1:		libgcrypt-1.8.5-detect-m32.patch
Patch5:		libgcrypt-1.9.1-i686-compile.patch
# (tpg) try to fix noexecstack with clang. This is very important to have noexecstack
Patch13:	libgcrypt-1.8.3-enable-noexecstack.patch
# (tpg) fix build with LLVM/clang
Patch14:	libgcrypt-1.8.3-fix-clang-optimization.patch
BuildRequires:	pkgconfig(gpg-error)
%if %{with compat32}
BuildRequires:	devel(libgpg-error)
BuildRequires:	libc6
%rename %{oldlib32name}
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

sed -i -e '/^sys_lib_dlsearch_path_spec/s,/lib /usr/lib,/usr/lib /lib64 /usr/lib64 /lib,g' libtool
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

# (tpg) strip LTO from "LLVM IR bitcode" files
check_convert_bitcode() {
    printf '%s\n' "Checking for LLVM IR bitcode"
    llvm_file_name=$(realpath ${1})
    llvm_file_type=$(file ${llvm_file_name})

    if printf '%s\n' "${llvm_file_type}" | grep -q "LLVM IR bitcode"; then
# recompile without LTO
    clang %{optflags} -fno-lto -Wno-unused-command-line-argument -x ir ${llvm_file_name} -c -o ${llvm_file_name}
    elif printf '%s\n' "${llvm_file_type}" | grep -q "current ar archive"; then
    printf '%s\n' "Unpacking ar archive ${llvm_file_name} to check for LLVM bitcode components."
# create archive stage for objects
    archive_stage=$(mktemp -d)
    archive=${llvm_file_name}
    cd ${archive_stage}
    ar x ${archive}
    for archived_file in $(find -not -type d); do
        check_convert_bitcode ${archived_file}
        printf '%s\n' "Repacking ${archived_file} into ${archive}."
        ar r ${archive} ${archived_file}
    done
    ranlib ${archive}
    cd ..
    fi
}

for i in $(find %{buildroot} -type f -name "*.[ao]"); do
    check_convert_bitcode ${i}
done

%files -n %{libname}
%{_libdir}/libgcrypt.so.%{major}*

%files -n %{devname}
%doc AUTHORS README* NEWS THANKS TODO ChangeLog
%{_bindir}/*
%{_includedir}/gcrypt.h
%{_libdir}/libgcrypt.so
%{_libdir}/pkgconfig/libgcrypt.pc
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
