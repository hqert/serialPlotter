# serialPlotter

Everything can be accessed as a library, but runnning the serialPlotter.py file executes the LiT demo program. The com port must be changed, and settings for the different subplots can be edited at the bottom of the file, in the main function. 

Each subplot has an associated callback used to get new data, it can be directly the serial interface or oa processing unit, which itself needs a callback as a data source. For now, the setup has one subplot w/ the raw input, and a second one w/ the filtered input, w/ the processing function also outputting the raw data.
