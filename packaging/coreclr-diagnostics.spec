%{!?dotnet_buildtype: %define dotnet_buildtype Release}

%define dotnet_version 6.0.9

Name:       coreclr-diagnostics
Version:    6.0.328102
Release:    0
Summary:    Microsoft .NET Core runtime diagnostic tools
Group:      Development/Languages
License:    MIT
URL:        https://github.com/dotnet/diagnostics
Source0:    %{name}-%{version}.tar.gz
Source1:    %{name}.manifest

BuildRequires: clang >= 3.8
BuildRequires: clang-devel >= 3.8
BuildRequires: cmake
BuildRequires: coreclr-devel
BuildRequires: corefx-managed
BuildRequires: gettext-tools
BuildRequires: libopenssl1.1-devel
BuildRequires: libstdc++-devel
BuildRequires: lldb >= 3.8
BuildRequires: lldb-devel >= 3.8
BuildRequires: llvm >= 3.8
BuildRequires: llvm-devel >= 3.8
BuildRequires: pkgconfig(libunwind)
BuildRequires: pkgconfig(lttng-ust)
BuildRequires: pkgconfig(uuid)
BuildRequires: python
BuildRequires: tizen-release

%ifarch armv7l
BuildRequires: python-accel-armv7l-cross-arm
BuildRequires: clang-accel-armv7l-cross-arm
BuildRequires: patchelf
%endif

%ifarch armv7hl
BuildRequires: python-accel-armv7hl-cross-arm
BuildRequires: clang-accel-armv7hl-cross-arm
BuildRequires: patchelf
%endif

%ifarch aarch64
BuildRequires: python-accel-aarch64-cross-aarch64
BuildRequires: clang-accel-aarch64-cross-aarch64
BuildRequires: patchelf
%endif

%ifarch %{ix86}
BuildRequires: patchelf
BuildRequires: glibc-64bit
BuildRequires: libgcc-64bit
BuildRequires: libopenssl11-64bit
BuildRequires: libstdc++-64bit
BuildRequires: libunwind-64bit
BuildRequires: libuuid-64bit
BuildRequires: zlib-64bit
%endif

AutoReq: 0
Requires: coreclr
Requires: corefx-managed
Requires: glibc
Requires: libgcc
Requires: libstdc++
Requires: libunwind
Requires: libuuid

%description
This package contains components for basic .NET debugging and diagnostic support.

%package tools
Summary:  Diagnostic tools
Requires: coreclr-diagnostics

%description tools
This package contains a collection of .NET diagnostic tools.

%prep
%setup -q -n %{name}-%{version}
cp %{SOURCE1} .

%ifarch armv7l armv7hl aarch64
# Detect interpreter name from cross-gcc
LD_INTERPRETER=$(patchelf --print-interpreter /emul/usr/bin/gcc)
LD_RPATH=$(patchelf --print-rpath /emul/usr/bin/gcc)
for file in $(find .dotnet -type f -name dotnet)
do
    patchelf --set-interpreter ${LD_INTERPRETER} ${file}
    patchelf --set-rpath ${LD_RPATH}:%{_builddir}/%{name}-%{version}/libicu-57.1/ ${file}
done
for file in $(find .dotnet libicu-57.1 -iname *.so -or -iname *.so.*)
do
    patchelf --set-rpath ${LD_RPATH}:%{_builddir}/%{name}-%{version}/libicu-57.1/ ${file}
done
%endif

%ifarch %{ix86}
for file in $(find .dotnet libicu-57.1 -iname *.so -or -iname *.so.*)
do
    patchelf --set-rpath %{_builddir}/%{name}-%{version}/libicu-57.1/ ${file}
done
%endif

%build
BASE_FLAGS=" --target=%{_host} "

%ifarch x86_64
# Even though build architectur is x86_64, it will be running on arm board.
# So we need to pass the arch argument as arm.
%define _barch  %{?cross:%{cross}}%{!?cross:x64}
%else
%ifarch aarch64
%define _barch  arm64
%else
%ifarch %{ix86}
%define _barch  x86
export CLANG_NO_LIBDIR_SUFFIX=1
BASE_FLAGS=$(echo $BASE_FLAGS | sed -e 's/--target=i686/--target=i586/')
BASE_FLAGS="$BASE_FLAGS -mstackrealign"
%else
%ifarch armv7l
%define _barch  armel
export CLANG_NO_LIBDIR_SUFFIX=1
%else
%ifarch armv7hl
%define _barch  arm
export CLANG_NO_LIBDIR_SUFFIX=1
%else

%endif
%endif
%endif
%endif
%endif

export CFLAGS=$BASE_FLAGS
export CXXFLAGS=$BASE_FLAGS
export ASMFLAGS="${BASE_FLAGS}"

%define _buildtype %{dotnet_buildtype}
%define _artifacts artifacts/bin

%ifarch armv7l armv7hl
%if %{dotnet_buildtype} == "Release"
export CXXFLAGS+="-fstack-protector-strong -D_FORTIFY_SOURCE=2"
%else
export CXXFLAGS+="-fstack-protector-strong"
%endif
%endif

export TIZEN_LOCAL_BUILD=1
export NUGET_PACKAGES=%{_builddir}/%{name}-%{version}/.packages
export LD_LIBRARY_PATH=%{_builddir}/%{name}-%{version}/libicu-57.1

./build.sh --portablebuild=false -configuration %{_buildtype} -architecture %{_barch} /p:NeedsPublishing=true /p:EnableSourceLink=false /p:EnableSourceControlManagerQueries=false

%install
%define diagnosticsdir   %{_datadir}/dotnet/shared/Microsoft.NETCore.App/%{dotnet_version}/SOS
%define toolsdir        /home/owner/share/.dotnet/tools

%ifarch x86_64
%define rid linux-x64
%else
%ifarch aarch64
%define rid linux-arm64
%else
%ifarch %{ix86}
%define rid linux-x86
%else
%ifarch armv7l armv7hl
%define rid linux-arm
%else

%endif
%endif
%endif
%endif

# SOS
mkdir -p %{buildroot}%{diagnosticsdir}
cp %{_artifacts}/Linux.%{_barch}.%{_buildtype}/*.so %{buildroot}%{diagnosticsdir}
cp %{_artifacts}/Linux.%{_barch}.%{_buildtype}/Microsoft.Bcl.AsyncInterfaces.dll %{buildroot}%{diagnosticsdir}
cp %{_artifacts}/Linux.%{_barch}.%{_buildtype}/Microsoft.Diagnostics.DebugServices.dll %{buildroot}%{diagnosticsdir}
cp %{_artifacts}/Linux.%{_barch}.%{_buildtype}/Microsoft.Diagnostics.DebugServices.Implementation.dll %{buildroot}%{diagnosticsdir}
cp %{_artifacts}/Linux.%{_barch}.%{_buildtype}/Microsoft.Diagnostics.ExtensionCommands.dll %{buildroot}%{diagnosticsdir}
cp %{_artifacts}/Linux.%{_barch}.%{_buildtype}/Microsoft.Diagnostics.NETCore.Client.dll %{buildroot}%{diagnosticsdir}
cp %{_artifacts}/Linux.%{_barch}.%{_buildtype}/Microsoft.Diagnostics.Runtime.dll %{buildroot}%{diagnosticsdir}
cp %{_artifacts}/Linux.%{_barch}.%{_buildtype}/Microsoft.Diagnostics.Runtime.Utilities.dll %{buildroot}%{diagnosticsdir}
cp %{_artifacts}/Linux.%{_barch}.%{_buildtype}/Microsoft.Extensions.Configuration.Abstractions.dll %{buildroot}%{diagnosticsdir}
cp %{_artifacts}/Linux.%{_barch}.%{_buildtype}/Microsoft.Extensions.Configuration.Binder.dll %{buildroot}%{diagnosticsdir}
cp %{_artifacts}/Linux.%{_barch}.%{_buildtype}/Microsoft.Extensions.Configuration.dll %{buildroot}%{diagnosticsdir}
cp %{_artifacts}/Linux.%{_barch}.%{_buildtype}/Microsoft.Extensions.DependencyInjection.Abstractions.dll %{buildroot}%{diagnosticsdir}
cp %{_artifacts}/Linux.%{_barch}.%{_buildtype}/Microsoft.Extensions.Logging.Abstractions.dll %{buildroot}%{diagnosticsdir}
cp %{_artifacts}/Linux.%{_barch}.%{_buildtype}/Microsoft.Extensions.Logging.dll %{buildroot}%{diagnosticsdir}
cp %{_artifacts}/Linux.%{_barch}.%{_buildtype}/Microsoft.Extensions.Options.dll %{buildroot}%{diagnosticsdir}
cp %{_artifacts}/Linux.%{_barch}.%{_buildtype}/Microsoft.Extensions.Primitives.dll %{buildroot}%{diagnosticsdir}
cp %{_artifacts}/Linux.%{_barch}.%{_buildtype}/Microsoft.FileFormats.dll %{buildroot}%{diagnosticsdir}
cp %{_artifacts}/Linux.%{_barch}.%{_buildtype}/Microsoft.SymbolStore.dll %{buildroot}%{diagnosticsdir}
cp %{_artifacts}/Linux.%{_barch}.%{_buildtype}/SOS.Extensions.dll %{buildroot}%{diagnosticsdir}
cp %{_artifacts}/Linux.%{_barch}.%{_buildtype}/SOS.Hosting.dll %{buildroot}%{diagnosticsdir}
cp %{_artifacts}/Linux.%{_barch}.%{_buildtype}/SOS.InstallHelper.dll %{buildroot}%{diagnosticsdir}
cp %{_artifacts}/Linux.%{_barch}.%{_buildtype}/System.CommandLine.dll %{buildroot}%{diagnosticsdir}
cp -f %{_artifacts}/Linux.%{_barch}.%{_buildtype}/sosdocsunix.txt %{buildroot}%{diagnosticsdir}

# Tools
mkdir -p %{buildroot}%{toolsdir}/%{rid}
cp %{_artifacts}/Linux.%{_barch}.%{_buildtype}/*.so %{buildroot}%{toolsdir}/%{rid}
for name in counters dump gcdump stack trace; do
  cp -f %{_artifacts}/dotnet-${name}/%{_buildtype}/netcoreapp*/publish/*.dll %{buildroot}%{toolsdir}
done
cp -f %{_artifacts}/dotnet-dump/%{_buildtype}/netcoreapp*/publish/*/sosdocsunix.txt %{buildroot}%{toolsdir}
# remove CoreCLR system DLLs
rm -f %{buildroot}%{toolsdir}/System.Collections.Immutable.dll
rm -f %{buildroot}%{toolsdir}/System.Reflection.Metadata.dll
rm -f %{buildroot}%{toolsdir}/System.Runtime.CompilerServices.Unsafe.dll


%files
%manifest %{name}.manifest
%{diagnosticsdir}/*

%files tools
%manifest %{name}.manifest
%defattr(644,owner,users,-)
%dir %{toolsdir}
%{toolsdir}/*

