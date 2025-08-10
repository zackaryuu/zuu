from src.zuu import scoop

def test_scoop_list_runs():
	result = scoop.scoop_list()
	assert isinstance(result, list)

def test_scoop_list_filter_runs():
	result = scoop.scoop_list_filter()
	assert isinstance(result, list)

def test_scoop_pkg_path_runs():
	out = scoop.scoop_pkg_path('python')
	assert (out is None) or hasattr(out, 'exists')

def test_scoop_pkg_manifest_path_runs():
	out = scoop.scoop_pkg_manifest_path('python')
	assert (out is None) or hasattr(out, 'exists')

def test_scoop_pkg_manifest_runs():
	out = scoop.scoop_pkg_manifest('python')
	assert (out is None) or isinstance(out, dict)
