from sqlalchemy.types import DateTime, Date, Time, String

playlist_types = {'datetime': DateTime,
                  'date': Date,
                  'time': Time,
                  'title': String(length=200),
                  # todo: finish declaring types
                  }
