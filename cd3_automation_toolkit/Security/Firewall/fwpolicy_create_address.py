#!/usr/bin/python3
# Copyright (c) 2016, 2019, Oracle and/or its affiliates. All rights reserved.
#
# This script will produce a Terraform file that will be used to set up OCI core components
# firewall, Listeners
#
# Author: Suruchi Singla
# Oracle Consulting
#
from oci.config import DEFAULT_LOCATION
from pathlib import Path
from commonTools import *
from jinja2 import Environment, FileSystemLoader
import os

######
# Required Inputs-CD3 excel file, Config file AND outdir
######

# Execution of the code begins here
def fwpolicy_create_address(inputfile, outdir, service_dir, prefix, ct):
    # Load the template file
    #print (inputfile, outdir, prefix, config, service_dir)
    file_loader = FileSystemLoader(f'{Path(__file__).parent}/templates')
    env = Environment(loader=file_loader, keep_trailing_newline=True)
    address = env.get_template('policy-addresslists-template')


    sheetName = "Firewall-Policy-AddressList"
    address_auto_tfvars_filename = prefix + "_"+sheetName.lower()+".auto.tfvars"

    filename = inputfile



    outfile = {}
    oname = {}
    address_tf_name = ''
    address_name = ''
    policy_name = ''
    address_str = {}
    address_names = {}
    policy_names = {}
    ip_id = {}

    # Read cd3 using pandas dataframe
    df, col_headers = commonTools.read_cd3(filename, sheetName)

    df = df.dropna(how='all')
    df = df.reset_index(drop=True)


    for reg in ct.all_regions:
        address_str[reg] = ''
        address_names[reg] = []
        resource = sheetName.lower()
        reg_out_dir = outdir + "/" + reg + "/" + service_dir
        commonTools.backup_file(reg_out_dir, resource, address_auto_tfvars_filename)


    # List of the column headers
    dfcolumns = df.columns.values.tolist()
    region_seen_so_far = []
    region_list = []

    for i in df.index:
        region = str(df.loc[i, 'Region'])
        region = region.strip().lower()
        if region.lower() != 'nan' and region in ct.all_regions:
            region = region.strip().lower()
            if region not in region_seen_so_far:
                region_list.append(region)
                region_seen_so_far.append(region)

        if region in commonTools.endNames:
            break

        if region != 'nan' and region not in ct.all_regions:
            print("\nInvalid Region; It should be one of the regions tenancy is subscribed to...Exiting!!")
            exit()




        # temporary dictionaries
        tempStr= {}
        tempdict= {}
        ip_id = ''

        # Fetch data; loop through columns
        for columnname in dfcolumns:

            # Column value
            columnvalue = str(df[columnname][i]).strip()

            # Check for boolean/null in column values
            columnvalue = commonTools.check_columnvalue(columnvalue)

            # Check for multivalued columns
            tempdict = commonTools.check_multivalues_columnvalue(columnvalue,columnname,tempdict)


            if columnname == "Firewall Policy":
                policy_tf_name = commonTools.check_tf_variable(columnvalue)
                tempdict = {'policy_tf_name': policy_tf_name}

            if columnname == "List Name":
                address_tf_name = commonTools.check_tf_variable(columnvalue)
                tempdict = {'address_tf_name': address_tf_name, 'address_name':columnvalue}

            if columnname == "Address List":
                    if columnvalue != '':
                        fw_ips = str(columnvalue).strip().split(",")
                        if len(fw_ips) == 1:
                            for ips in fw_ips:
                                ip_id = "\"" + ips.strip() + "\""

                        elif len(fw_ips) >= 2:
                            c = 1
                            for ips in fw_ips:
                                data = "\"" + ips.strip() + "\""

                                if c == len(fw_ips):
                                    ip_id = ip_id + data
                                else:
                                    ip_id = ip_id + data + ","
                                c += 1
                    columnvalue = ip_id

                    tempdict = {'address_list': ip_id}


            columnname = commonTools.check_column_headers(columnname)
            tempStr[columnname] = str(columnvalue).strip()
            tempStr.update(tempdict)


        address_str[region] = address_str[region] + address.render(tempStr)


    for reg in region_list:
        reg_out_dir = outdir + "/" + reg + "/" + service_dir
        if not os.path.exists(reg_out_dir):
            os.makedirs(reg_out_dir)
        outfile[reg] = reg_out_dir + "/" + address_auto_tfvars_filename

        if address_str[reg] != '':
            # Generate Final String
            src = "##Add New addresses for " + reg.lower() + " here##"
            address_str[reg] = address.render(count=0, region=reg).replace(src, address_str[reg] + "\n" + src)
            address_str[reg] = "".join([s for s in address_str[reg].strip().splitlines(True) if s.strip("\r\n").strip()])
            address_str[reg] = "\n\n" + address_str[reg]
            oname[reg] = open(outfile[reg], 'a')
            oname[reg].write(address_str[reg])
            oname[reg].close()
            print(outfile[reg] + " containing TF for Firewall Policy address lists has been updated for region " + reg)
