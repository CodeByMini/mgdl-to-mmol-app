from datetime import datetime


def parsera(output_file, input_file, time_format):
    f = open(input_file + ".csv")

    dates = []
    values = []
    days = []
    for line in f:
        item = line.split(";")
        dates.append(datetime.strptime(item[0], time_format))
        values.append(float(item[1]) / 18)

    # writer = StringIO()
    outfile = open(output_file + ".csv", "w")

    firstrow = "Glukosuppgifter,Skapat den,,Skapat av,\n"
    secondrow = "Enhet,Serienummer,Enhetens tidsstämpel,Registertyp,Historiskt glukosvärde mmol/L,Skanna glukosvärde mmol/L,Icke-numeriskt snabbverkande insulin,Snabbverkande insulin (enheter),Icke-numerisk mat,Kolhydrater (gram),Kolhydrater (portioner),Icke-numeriskt långtidsverkande insulin,Långtidsverkande insulin (enheter),Anteckningar,Glukossticka mmol/L,Keton mmol/L,Måltidsinsulin (enheter),Korrigeringsinsulin (enheter),Användarändrat insulin (enheter)\n"

    serial_str = "SOME_SERIAL_NUMBER"
    outfile.write(firstrow)
    outfile.write(secondrow)
    for i in range(len(dates)):
        print(dates[i])
        date = dates[i].strftime("%m-%d-%Y %H:%M")
        value = str(values[i])

        row = (
            "Freestyle Libre,"
            + serial_str
            + ","
            + date
            + ',0,"'
            + value
            + '",,,'
            + ",,,,,,,,,,,\n"
        )

        outfile.write(row)

    outfile.close()
    print(days)


if __name__ == "__main__":
    time_format = "%Y-%m-%dT%H:%M:%S"
    input_file = "input.csv"
    output_file = "output.csv"

    parsera(output_file, input_file, time_format)
