# Load user data from JSON file
import json
from pathlib import Path
from .models import StoredUsers, StoredUser, Username, DatabaseV1, Roles

__all__ = ["user_store", "load_user_data", "save_user_data", "UserStore", "USER_DATA_FILE"]


USER_DATA_FILE = Path("user_data.json")


def load_user_data(data_file: Path) -> StoredUsers:
    if data_file.exists():
        with open(data_file, "r") as f:
            user_data = json.load(f)
            user_data = DatabaseV1(**user_data)
        # end with
    else:
        user_data = DatabaseV1(
            users={
                "admin": StoredUser(
                    password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "password"
                    roles=[Roles.ADMIN],
                ),
            },
        )

        data_file.parent.mkdir(parents=True, exist_ok=True)
        with open(data_file, "w") as f:
            json.dump(user_data, f)
        # end with
    # end if

    return user_data.users
# end def


def save_user_data(data_file: Path, user_data: StoredUsers):
    with open(file=data_file, mode="w") as f:
        json.dump(
            obj=DatabaseV1(users=user_data).model_dump(
                mode="json",
            ),
            fp=f,
            ensure_ascii=False,
            indent=2,
        )
    # end with
# end def


class UserStore():
    def __init__(self, data_file: Path):
        self.data_file = data_file
        self.user_data = load_user_data(self.data_file)

        self.load_user_data()
    # end def

    def load_user_data(self):
        self.user_data = load_user_data(self.data_file)
    # end def

    def save_user_data(self):
        save_user_data(self.data_file, self.user_data)
    # end def

    def has(self, user: Username):
        return user in self.user_data
    # end def

    def get(self, user: Username, default=None):
        return self.user_data.get(user, default)
    # end def

    def set(self, user: Username, data: StoredUser):
        self.user_data.update({user: data})
        self.save_user_data()
    # end def

    def __setitem__(self, user: Username, data: StoredUser):
        self.set(user, data)
    # end def

    def __getitem__(self, user: Username):
        return self.get(user)
    # end def

    def __contains__(self, user: Username):
        return self.has(user)
    # end def
# end class


user_store = UserStore(USER_DATA_FILE)
