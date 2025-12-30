from django.contrib.auth.base_user import BaseUserManager

class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, username: str, password: str = None, name: str = ""):
        if not username:
            raise ValueError("username is required")
        username = username.strip().lower()

        user = self.model(username=username, name=name or "")
        user.set_password(password)
        user.is_active = True
        user.save(using=self._db)
        return user

    def create_superuser(self, username: str, password: str, name: str = ""):
        user = self.create_user(username=username, password=password, name=name or "Admin")
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user
