#!/usr/bin/env python3
import os
import platform
import subprocess
import shutil
import glob

def run_command(args, shell=False):
    kargs = {'check': True}
    try:
        subprocess.run(args, **kargs)
    except:
        if isinstance(args, list):
            args = ' '.join(args)
        subprocess.run(args, shell=True, **kargs)

def get_arch_name():
    arch_dict = {
        'x86_64': 'amd64',
        'aarch64': 'arm64'
    }
    arch = platform.machine()
    if arch in arch_dict:
        return arch_dict[arch]
    return 'any'

def create_deb_package():
    run_command('pip3 install meson --user') # apt does not have a proper version of meson yet.
    
    src_dir = os.getcwd()

    # Read version
    version = ""
    version_file = open('version.txt', 'r')
    for line in version_file.read().splitlines():
      if line.find('VERSION_MAJOR') != -1:
        version = line.split(' ')[-1]
      elif line.find('VERSION_MINOR') != -1:
        version = version + "." + line.split(' ')[-1]
      elif line.find('VERSION_PATCH') != -1:
        version = version + "."  + line.split(' ')[-1]
      elif line.find('VERSION_GIT_DATE') != -1:
        version = version + "."  + line.split(' ')[-1]
        break
    # Prepare variables
    arch = get_arch_name()
    pkg_name = os.path.basename(src_dir)
    pkg_fullname = '_'.join([pkg_name, version, arch])
    stage_dir = os.path.join(src_dir, pkg_fullname)
    shutil.copytree(os.path.join(src_dir, 'debian_template'), stage_dir)
    temp_dir = os.path.join(src_dir, 'temp_install')
    # Build
    run_command(['meson', 'setup', 'build',
     '--buildtype=release', 
     '-DPISTACHE_BUILD_EXAMPLES=false',
     '-DPISTACHE_BUILD_TESTS=false',
     '-DPISTACHE_BUILD_DOCS=false',
     '-DPISTACHE_USE_SSL=True',
     f'--prefix={temp_dir}'
     ])
    run_command(['meson', 'compile', '-C build'])
    run_command(['meson', 'install', '-C build'])
    # Make debian package folder
    shutil.copytree(os.path.join(temp_dir, 'include/pistache'), os.path.join(stage_dir, 'usr/local/include/pistache'))
    src_lib_path = os.path.join(temp_dir, 'lib', platform.machine(), '-linux-gnu')
    dst_lib_path = os.path.join(stage_dir, 'usr/local/lib')
    for item in os.listdir(src_lib_path):
      s = os.path.join(src_lib_path, item)
      d = os.path.join(dst_lib_path, item)
      if os.path.isdir(s) == False:
        shutil.copy2(s, d, follow_symlinks=False) 

    # Update debian control file.
    debinfo_dir = os.path.join(stage_dir, 'DEBIAN')
    debinfo = [
        ('Package', pkg_name),
        ('Version', version),
        ('Architecture', arch),
        ('Maintainer', 'seoulrobotics (support@seoulrobotics.org)'),
        ('Description', 'This package is not built by the authors but by seoulrobotics.')
    ]
    with open(os.path.join(debinfo_dir, 'control'), 'w') as fp:
        fp.writelines([f'{k}: {v}\n' for k, v in debinfo])

    # Replace version in pkgconfig file.
    pkgconfig_file = os.path.join(stage_dir, 'usr/local/lib/pkgconfig/libpistache.pc')

    fin = open(pkgconfig_file, "rt")
    data = fin.read()
    data = data.replace('#REPLACE_VER', version)
    fin.close()
    fin = open(pkgconfig_file, "wt")
    fin.write(data)
    fin.close()

    run_command(['dpkg-deb', '--build', pkg_fullname])

    shutil.rmtree(temp_dir)
    shutil.rmtree(stage_dir)
    shutil.rmtree(os.path.join(src_dir, 'build'))

if __name__ == '__main__':
  deb_path = create_deb_package()