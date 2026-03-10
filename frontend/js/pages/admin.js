(function () {
  const token = localStorage.getItem("lager_token");
  const userRaw = localStorage.getItem("lager_user");

  if (!token || !userRaw) {
    window.location.href = "/";
    return;
  }

  try {
    const user = JSON.parse(userRaw);
    if (!user.is_admin) {
      window.location.href = "/lager";
    }
  } catch {
    window.location.href = "/";
  }
})();
