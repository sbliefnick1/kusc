from sqlalchemy.types import DateTime, Date, Time, String, JSON

playlist_types = {'air_datetime': DateTime,
                  'air_date': Date,
                  'air_time': Time,
                  'title': String(length=200),
                  # todo: finish declaring types
                  }
