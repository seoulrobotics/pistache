#!/usr/bin/env python3
import os
import platform
import subprocess
import shutil

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

# https://linuxconfig.org/easy-way-to-create-a-debian-package-and-local-package-repository
# def create_deb_package(root_dir, repo_url, cursor:str = ''):
#     src_dir = component.get_source(repo_url, root_dir, cursor=cursor)

#     os.chdir(src_dir)
#     if not cursor:
#         cmd_get_tag = 'git describe --tags --exact-match 2> /dev/null'
#         cursor = subprocess.run(cmd_get_tag, shell=True).stdout

#         if not cursor:
#             cursor = '0.0.1' # set an arbitrary version number

#     cursor = re.sub('[a-zA-Z]', '', cursor) # version should not have any alphabet.
#     arch = install.get_arch_name()

#     pkg_name = os.path.basename(src_dir)
#     pkg_fullname = '_'.join([pkg_name, cursor, arch])
#     stage_dir = os.path.join(src_dir, pkg_fullname)

#     build_dir = install.build_cmake_project(src_dir)

#     os.chdir(build_dir)
#     install.run_command(['make', f'DESTDIR={stage_dir}', 'install'])

#     # Note: some packages have different .so file names from their own names.
#     #       e.g., LightGBM: lib_lightgbm.so
#     #       Let's pray for luck in the case
#     root_lib_dir = os.path.join(stage_dir, 'usr/local/lib')
#     target_lib_path = os.path.join(root_lib_dir, f'lib{pkg_name}.so')

#     if not os.path.exists(target_lib_path):
#         lib_pattern = os.path.join(root_lib_dir, '**', f'lib{pkg_name}.so*')

#         libs = glob.glob(lib_pattern, recursive=True)
#         for source_lib in libs:
#             if not os.path.islink(source_lib):
#                 os.symlink(os.path.relpath(source_lib, root_lib_dir), target_lib_path)

#     debinfo_dir = os.path.join(stage_dir, 'DEBIAN')
#     os.makedirs(debinfo_dir)

#     # use list to keep the items ordered
#     debinfo = [
#         ('Package', pkg_name),
#         ('Version', cursor),
#         ('Architecture', arch),
#         ('Maintainer', 'seoulrobotics (support@seoulrobotics.org)'),
#         ('Description', 'This package is not built by the authors but by seoulrobotics.')
#     ]

#     with open(os.path.join(debinfo_dir, 'control'), 'w') as fp:
#         fp.writelines([f'{k}: {v}\n' for k, v in debinfo])

#     os.chdir(src_dir)
#     install.run_command(['dpkg-deb', '--build', pkg_fullname])

#     shutil.move(os.path.join(src_dir, pkg_fullname + '.deb'), root_dir)

#     return os.path.join(root_dir, pkg_fullname + '.deb')

def create_deb_package(root_dir, repo_url, cursor:str = ''):
    #run_command('pip3 install meson --user') # apt does not have a proper version of meson yet.
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
    arch = get_arch_name()
    pkg_name = os.path.basename(src_dir)
    pkg_fullname = '_'.join([pkg_name, version, arch])
    stage_dir = os.path.join(src_dir, pkg_fullname)
    shutil.copytree(os.path.join(src_dir, 'debian_template'), stage_dir)
    temp_dir = os.path.join(src_dir, 'temp_install')
    run_command(['meson', 'setup', 'build',
     '--buildtype=release',
     f'--prefix={temp_dir}'
     ])
    run_command(['meson', 'compile', '-C build'])
    shutil.copytree(os.path.join(stage_dir, 'include'), os.path.join(stage_dir, 'usr/local/include'))
    shutil.copytree(os.path.join(stage_dir, 'lib/x86_64-linux-gnu'), os.path.join(stage_dir, 'usr/local/lib'))
    #run_command(['meson', 'install', '-C build'])
   

    # source = "/parent/subdir"
    # destination = "/parent/"
    # files_list = os.listdir(source)
    # for files in files_list:
    #     shutil.move(files, destination)

    # for filename in os.listdir(os.path.join(temp_dir, 'slave')):
    #     shutil.move(os.path.join(temp_dir, 'slave', filename), os.path.join(temp_dir, filename))
    # os.rmdir(temp_dir)
    # # Note: some packages have different .so file names from their own names.
    # #       e.g., LightGBM: lib_lightgbm.so
    # #       Let's pray for luck in the case
    # root_lib_dir = os.path.join(stage_dir, '/lib/x86_64-linux-gnu')
    # target_lib_path = os.path.join(os.path.join(stage_dir, '/usr/local/lib'), f'lib{pkg_name}.so')

    # if not os.path.exists(target_lib_path):
    #     lib_pattern = os.path.join(root_lib_dir, '**', f'lib{pkg_name}.so*')

    #     libs = glob.glob(lib_pattern, recursive=True)
    #     for source_lib in libs:
    #         if not os.path.islink(source_lib):
    #             os.symlink(os.path.relpath(source_lib, root_lib_dir), target_lib_path)

    debinfo_dir = os.path.join(stage_dir, 'DEBIAN')

    # use list to keep the items ordered
    debinfo = [
        ('Package', pkg_name),
        ('Version', version),
        ('Architecture', arch),
        ('Maintainer', 'seoulrobotics (support@seoulrobotics.org)'),
        ('Description', 'This package is not built by the authors but by seoulrobotics.')
    ]

    with open(os.path.join(debinfo_dir, 'control'), 'w') as fp:
        fp.writelines([f'{k}: {v}\n' for k, v in debinfo])
    run_command(['dpkg-deb', '--build', pkg_fullname])

    #shutil.move(os.path.join(src_dir, pkg_fullname + '.deb'), root_dir)


if __name__ == '__main__':
  cwd = os.getcwd()

  deb_path = create_deb_package(cwd, 'repo_url', cursor='cursor')