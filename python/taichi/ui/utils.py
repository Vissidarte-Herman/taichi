import platform
import re
from math import acos, asin, cos, sin

from taichi._lib import core as _ti_core
from taichi.lang.impl import default_cfg
from taichi.lang.matrix import Vector


def get_field_info(field):
    info = _ti_core.FieldInfo()
    if field is None:
        info.valid = False
        return info
    info.valid = True
    if default_cfg().arch == _ti_core.cuda:
        info.field_source = _ti_core.FieldSource.TaichiCuda
    elif default_cfg().arch == _ti_core.x64:
        info.field_source = _ti_core.FieldSource.TaichiX64
    elif default_cfg().arch == _ti_core.arm64:
        info.field_source = _ti_core.FieldSource.TaichiX64
    elif default_cfg().arch == _ti_core.vulkan:
        info.field_source = _ti_core.FieldSource.TaichiVulkan
    else:
        raise Exception("unsupported taichi backend")
    info.shape = [n for n in field.shape]

    info.dtype = field.dtype
    info.snode = field.snode.ptr

    if hasattr(field, 'n'):
        info.field_type = _ti_core.FieldType.Matrix
        info.matrix_rows = field.n
        info.matrix_cols = field.m
    else:
        info.field_type = _ti_core.FieldType.Scalar
        info.matrix_rows = 1
        info.matrix_cols = 1
    return info


def euler_to_vec(yaw, pitch):
    v = Vector([0.0, 0.0, 0.0])
    v[0] = -sin(yaw) * cos(pitch)
    v[1] = sin(pitch)
    v[2] = -cos(yaw) * cos(pitch)
    return v


def vec_to_euler(v):
    v = v.normalized()
    pitch = asin(v[1])

    sin_yaw = -v[0] / cos(pitch)
    cos_yaw = -v[2] / cos(pitch)

    eps = 1e-6

    if abs(sin_yaw) < eps:
        yaw = 0
    else:
        yaw = acos(cos_yaw)
        if sin_yaw < 0:
            yaw = -yaw

    return yaw, pitch


def try_get_wheel_tag(module):
    try:
        import wheel.metadata  # pylint: disable=import-outside-toplevel
        wheel_path = f'{module.__path__[0]}-{".".join(map(str, module.__version__))}.dist-info/WHEEL'
        meta = wheel.metadata.read_pkg_info(wheel_path)
        return meta.get('Tag')
    except Exception:
        return None


def try_get_loaded_libc_version():
    assert platform.system() == "Linux"
    with open('/proc/self/maps') as f:
        content = f.read()

    try:
        libc_path = next(v for v in content.split() if 'libc-' in v)
        ver = re.findall(r'\d+\.\d+', libc_path)
        if not ver:
            return None
        return tuple([int(v) for v in ver[0].split('.')])
    except StopIteration:
        return None


class GGUINotAvailableException(Exception):
    pass


def check_ggui_availability():
    """Checks if the `GGUI` environment is available.
    """
    if _ti_core.GGUI_AVAILABLE:
        return

    try:
        # Try identifying the reason
        import taichi  # pylint: disable=import-outside-toplevel
        wheel_tag = try_get_wheel_tag(taichi)
        if platform.system(
        ) == "Linux" and wheel_tag and 'manylinux2014' in wheel_tag:
            libc_ver = try_get_loaded_libc_version()
            if libc_ver and libc_ver < (2, 27):
                raise GGUINotAvailableException(
                    "GGUI is not available since you have installed a restricted version of taichi. "
                    "Your OS is outdated, try upgrading to a recent one (e.g. Ubuntu 18.04 or later) if possible."
                )

            try:
                import pip  # pylint: disable=import-outside-toplevel
                ver = tuple([int(v) for v in pip.__version__.split('.')])
                if ver < (20, 3, 0):
                    raise GGUINotAvailableException(
                        "GGUI is not available since you have installed a restricted version of taichi. "
                        f"Your pip (version {pip.__version__}) is outdated (20.3.0 or later required), "
                        "try upgrading pip and install taichi again.")
            except ImportError:
                pass

            raise GGUINotAvailableException(
                "GGUI is not available since you have installed a restricted version of taichi."
            )

    except GGUINotAvailableException:
        raise

    except Exception:
        pass

    raise GGUINotAvailableException("GGUI is not available.")
