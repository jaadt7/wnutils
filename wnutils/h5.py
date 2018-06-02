import wnutils.base as wnb
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import warnings
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=FutureWarning)
    import h5py


class H5(wnb.Base):
    """A class for reading and plotting webnucleo HDF5 files.

       Each instance corresponds to an hdf5 file.  Methods extract
       data and plot data from the file.

       Args:
           ``file`` (:obj:`str`): The name of the hdf5 file.

       """

    def __init__(self, file):
        self._h5file = h5py.File(file, 'r')

    def _get_group_zone_property_hash(self, group, zone_index):

        properties = (
            self._h5file['/' + group + '/Zone Properties/' + str(zone_index)]
        )

        result = {}

        for property in properties:
            p0 = property[0].decode('ascii')
            p1 = property[1].decode('ascii')
            p2 = property[2].decode('ascii')
            name = ''
            if(p1 == '0' and p2 == '0'):
                name = p0
            elif(p1 != '0' and p2 == '0'):
                name = (p0, p1)
            else:
                name = (p0, p1, p2)
            result[name] = property[3].decode('ascii')

        return result

    def get_zone_labels_for_group(self, group):
        """Method to return the zone labels for a group in a webnucleo hdf5 file.

        Args:
            ``group`` (:obj:`str`): The name of the group.

        Returns:
            :obj:`list`: A list of :obj:`tuple` giving the labels for the
            zones in a group.

        """


        zone_labels = self._h5file['/' + group + '/Zone Labels']

        result = []

        for i in range(len(zone_labels)):
            result.append(
                (
                    zone_labels[i][0].decode('ascii'),
                    zone_labels[i][1].decode('ascii'),
                    zone_labels[i][2].decode('ascii')
                )
            )

        return result

    def _get_group_zone_labels_hash(self, group):

        zone_labels_array = self.get_zone_labels_for_group(group)

        result = {}

        for i in range(len(zone_labels_array)):
            result[zone_labels_array[i]] = i

        return result

    def get_iterable_groups(self):
        """Method to return the non-nuclide data groups in an hdf5 file.

        Returns:
            :obj:`list`: A list of strings giving the names of the groups.

        """

        result = []

        for group_name in self._h5file:
            if(group_name != 'Nuclide Data'):
                result.append(group_name)

        return result

    def _get_nuclide_data_array(self):

        result = []

        nuclide_data = self._h5file['/Nuclide Data']

        for i in range(len(nuclide_data)):
            data = {}
            data['name'] = nuclide_data[i][0].decode('ascii')
            data['z'] = nuclide_data[i][2]
            data['a'] = nuclide_data[i][3]
            data['source'] = nuclide_data[i][4].decode('ascii')
            data['state'] = nuclide_data[i][5].decode('ascii')
            data['spin'] = nuclide_data[i][6]
            data['mass excess'] = nuclide_data[i][7]
            result.append(data)

        return result

    def get_nuclide_data(self):
        """Method to return nuclide data from an hdf5 file.

        Returns:

            :obj:`dict`: A dictionary of the nuclide data.  Each
            entry is itself a dictionary containing the nuclide's index,
            name, z, a, source (data source), state, spin, and mass excess.

        """

        nuclide_data = self._get_nuclide_data_array()

        result = {}

        for i in range(len(nuclide_data)):
            data = {}
            data['index'] = i
            data['z'] = nuclide_data[i]['z']
            data['a'] = nuclide_data[i]['a']
            data['source'] = nuclide_data[i]['source']
            data['state'] = nuclide_data[i]['state']
            data['mass excess'] = nuclide_data[i]['mass excess']
            data['spin'] = nuclide_data[i]['spin']
            result[nuclide_data[i]['name']] = data

        return result

    def get_group_mass_fractions(self, group):
        """Method to return mass fractions from a group in an hdf5 file.

            Args:
                ``group`` (:obj:`str`): The name of the group.

            Returns:
                :obj:`h5py:Dataset`: A 2d hdf5 dataset.  The first index
                indicates the zone and the second the species.

        """

        return self._h5file['/' + group + '/Mass Fractions']

    def get_zone_mass_fractions_in_groups(self, zone, nuclides):
        """Method to return zone mass fractions in all groups.

        Args:

            ``zone`` (:obj:`tuple`): A three element tuple giving the three
            labels for the zone.

            ``nuclides`` (:obj:`list`): A list of strings giving the nuclides
            whose mass fractions are to be retrieved.

        Returns:
            :obj:`dict`: A dictionary of :obj:`numpy.array` giving the
            mass fractions in the groups.

        """

        nuclide_hash = self.get_nuclide_data()

        result = {}

        for nuclide in nuclides:
            result[nuclide] = np.array([])

        for group_name in self.get_iterable_groups():
            zone_index = self._get_group_zone_labels_hash(group_name)
            x = self.get_group_mass_fractions(group_name)
            for nuclide in nuclides:
                result[nuclide] = np.append(
                    result[nuclide],
                    x[zone_index[zone], nuclide_hash[nuclide]['index']]
                )

        return result

    def get_zone_properties_in_groups(self, zone, properties):
        """Method to return zone properties in all groups.

        Args:

            ``zone`` (:obj:`tuple`): A three element tuple giving the three
            labels for the zone.

            ``properties`` (:obj:`list`): A list of strings giving the
            properties to be retrieved.

        Returns:
            :obj:`dict`: A dictionary of :obj:`list` giving the properties
            in the groups as strings.

        """

        result = {}

        for property in properties:
            result[property] = []

        for group_name in self.get_iterable_groups():
            zone_index = self._get_group_zone_labels_hash(group_name)[zone]
            p = self. _get_group_zone_property_hash(group_name, zone_index)
            for property in properties:
                result[property].append(p[property])

        return result

    def get_zone_properties_in_groups_as_floats(self, zone, properties):
        """Method to return zone properties in all groups as floats.

        Args:

            ``zone`` (:obj:`tuple`): A three element tuple giving the three
            labels for the zone.

            ``properties`` (:obj:`list`): A list of strings giving the
            properties to be retrieved.

        Returns:
            :obj:`dict`: A dictionary of :obj:`numpy.array` giving the
            properties in the groups as floats.

        """

        result = {}

        props = self.get_zone_properties_in_groups(zone, properties)

        for prop in props:
            result[prop] = np.array(props[prop], np.float_)

        return result

    def get_group_properties_in_zones(self, group, properties):
        """Method to return properties in all zones for a group.

        Args:

            ``group`` (:obj:`str`): A string giving the group name.

            ``properties`` (:obj:`list`): A list of strings giving the
            properties to be retrieved.

        Returns:
            :obj:`dict`: A dictionary of :obj:`list` giving the
            properties in the zones as strings.

        """

        result = {}

        for property in properties:
            result[property] = []

        zone_labels_hash = self._get_group_zone_labels_hash(group)

        for zone_labels in self.get_zone_labels_for_group(group):
            p = (
                self._get_group_zone_property_hash(
                    group, zone_labels_hash[
                        (zone_labels[0], zone_labels[1], zone_labels[2])
                    ]
                )
            )
            for property in properties:
                result[property].append(p[property])

        return result

    def get_group_properties_in_zones_as_floats(self, group, properties):
        """Method to return properties in all zones for a group as floats.

        Args:

            ``group`` (:obj:`str`): A string giving the group name.

            ``properties`` (:obj:`list`): A list of strings giving the
            properties to be retrieved.

        Returns:
            :obj:`dict`: A dictionary of :obj:`numpy.array` giving the
            properties in the zones as floats.

        """

        result = {}

        props = self.get_group_properties_in_zones(group, properties)

        for prop in props:
            result[prop] = np.array(props[prop], np.float_)

        return result

    def plot_zone_property_vs_property(
        self, zone, prop1, prop2, xfactor=1, yfactor=1, rcParams=None,
        **kwargs
    ):
        """Method to plot a property vs. a property in a zone.

        Args:

            ``zone`` (:obj:`tuple`): A three element tuple giving the zone
            labels.

            ``prop1`` (:obj:`str`): A string giving the property (which will
            be the abscissa of the plot).

            ``prop2`` (:obj:`str`): A string giving the property (which will
            be the ordinate of the plot).

            ``xfactor`` (:obj:`float`, optional): A float giving the scaling
            for the abscissa values.  Defaults to 1.

            ``yfactor`` (:obj:`float`, optional): A float giving the scaling
            for the ordinate values.  Defaults to 1.

            ``rcParams`` (:obj:`dict`, optional): A dictionary of
            :obj:`matplotlib.rcParams` to be applied to the plot.
            Defaults to leaving the current rcParams unchanged.

            ``**kwargs``:  Acceptable :obj:`matplotlib.pyplot` functions.
            Include directly, as a :obj:`dict`, or both.

        Returns:
            A matplotlib plot.

        """

        self.set_plot_params(mpl, rcParams)

        result = (
            self.get_zone_properties_in_groups_as_floats(zone, [prop1, prop2])
        )

        self.apply_class_methods(plt, kwargs)

        plt.plot(result[prop1] / xfactor, result[prop2] / yfactor)
        plt.show()

    def plot_group_mass_fractions(
        self, group, species, use_latex_names=False, rcParams=None, **kwargs
    ):
        """Method to plot group mass fractions vs. zone.

        Args:

            ``group`` (:obj:`str`): A string giving the group.

            ``species`` (:obj:`list`): A list of strings giving the species to
            plot.

            ``use_latex_names`` (:obj:`bool`, optional): If set to True,
            species names converted to latex format.

            ``rcParams``` (:obj:`dict`, optional): A dictionary of
            :obj:`matplotlib.rcParams` to be applied to the plot.
            Defaults to leaving the current rcParams unchanged.

            ``**kwargs``:  Acceptable :obj:`matplotlib.pyplot` functions.
            Include directly, as a :obj:`dict`, or both.

        Returns:
            A matplotlib plot.

        """

        self.set_plot_params(mpl, rcParams)

        fig = plt.figure()

        l = []
        latex_names = []

        m = self.get_group_mass_fractions(group)

        nuclide_data = self.get_nuclide_data()

        if use_latex_names:
            laxtex_names = self.get_latex_names(species)

        iy = 0
        for sp in species:
            if(len(latex_names) != 0):
                lab = latex_names[sp]
            else:
                lab = sp
            l.append(plt.plot(m[:, nuclide_data[sp]['index']], label=lab))

        if(len(species) != 1):
            plt.legend()

        if('ylabel' not in kwargs):
            if(len(species) != 1):
                plt.ylabel('Mass Fraction')
            else:
                if(len(latex_names) == 0):
                    plt.ylabel('X(' + species[0] + ')')
                else:
                    plt.ylabel('X(' + latex_names[species[0]] + ')')

        self.apply_class_methods(plt, kwargs)

        plt.show()

    def plot_group_mass_fractions_vs_property(
        self, group, prop, species, xfactor=1, use_latex_names=False,
        rcParams=None, **kwargs
    ):
        """Method to plot group mass fractions vs. zone property.

        Args:

            ``group`` (:obj:`str`): A string giving the group.

            ``prop`` (:obj:`str`): A string giving the property (which will
            serve as the plot abscissa).

            ``species`` (:obj:`list`): A list of strings giving the species
            to plot.

            ``xfactor`` (:obj:`float`, optional): A float giving the scaling
            for the abscissa values.  Defaults to 1.

            ``use_latex_names`` (:obj:`bool`, optional): If set to True,
            species names converted to latex format.

            ``rcParams``` (:obj:`dict`, optional): A dictionary of
            :obj:`matplotlib.rcParams` to be applied to the plot.
            Defaults to leaving the current rcParams unchanged.

            ``**kwargs``:  Acceptable :obj:`matplotlib.pyplot` functions.
            Include directly, as a :obj:`dict`, or both.

        Returns:
            A matplotlib plot.

        """

        plp.set_plot_params(mpl, rcParams)

        fig = plt.figure()

        l = []
        latex_names = []

        x = self.get_group_properties_in_zones_as_floats(
            group, [prop]
        )[prop]
        m = self.get_group_mass_fractions(group)

        nuclide_data = self.get_nuclide_data()

        if use_latex_names:
            laxtex_names = self.get_latex_names(species)

        iy = 0
        for sp in species:
            y = m[:, nuclide_data[sp]['index']]
            if(len(latex_names) != 0):
                lab = latex_names[sp]
            else:
                lab = sp
            l.append(plt.plot(x / xfactor, y, label=lab))

        if(len(species) != 1):
            plt.legend()

        if('ylabel' not in kwargs):
            if(len(species) != 1):
                plt.ylabel('Mass Fraction')
            else:
                if(len(latex_names) == 0):
                    plt.ylabel('X(' + species[0] + ')')
                else:
                    plt.ylabel('X(' + latex_names[species[0]] + ')')

        if('xlabel' not in kwargs):
            plt.xlabel(prop)

        self.apply_class_methods(plt, kwargs)

        plt.show()

    def plot_zone_mass_fractions_vs_property(
        self, zone, prop, species, xfactor=1, yfactor=None,
        use_latex_names=False, rcParams=None, **kwargs
    ):
        """Method to plot zone mass fractions vs. zone property.

        Args:

            ``zone`` (:obj:`tuple`): A three element tuple giving the zone.

            ``prop`` (:obj:`str`): A string giving the property (which will
            serve as the plot abscissa).

            ``species`` (:obj:`list`): A list of strings giving the species
            to plot.

            ``xfactor`` (:obj:`float`, optional): A float giving the scaling
            for the abscissa values.  Defaults to 1.

            ``yfactor`` (:obj:`list`, optional): A list of floats giving
            factor by which to scale the mass fractions.  Defaults to not
            scaling.  If supplied, must by the same length as ``species``.

            ``use_latex_names`` (:obj:`bool`, optional): If set to True,
            species names converted to latex format.

            ``rcParams`` (:obj:`dict`, optional): A dictionary of
            :obj:`matplotlib.rcParams` to be applied to the plot.
            Defaults to leaving the current rcParams unchanged.

            ``**kwargs``:  Acceptable :obj:`matplotlib.pyplot` functions.
            Include directly, as a :obj:`dict`, or both.

        Returns:
            A matplotlib plot.

        """

        self.set_plot_params(mpl, rcParams)

        fig = plt.figure()

        l = []
        latex_names = []

        x = self.get_zone_properties_in_groups_as_floats(zone, [prop])[prop]
        m = self.get_zone_mass_fractions_in_groups(zone, species)

        if yfactor:
            if len(yfactor) != len(species):
                print(
                    'yfactor length must be the same as the number of species.'
                )
                return
        else:
            yfactor = np.full(len(species), 1.)

        if use_latex_names:
            latex_names = self.get_latex_names(species)

        for i in range(len(species)):
            if(len(latex_names) != 0):
                lab = latex_names[species[i]]
            else:
                lab = species[i]
            l.append(
                plt.plot(x / xfactor, m[species[i]] / yfactor[i], label=lab)
            )

        if(len(species) != 1):
            plt.legend()

        if('ylabel' not in kwargs):
            if(len(species) != 1):
                plt.ylabel('Mass Fraction')
            else:
                if(len(latex_names) == 0):
                    plt.ylabel('X(' + species[0] + ')')
                else:
                    plt.ylabel('X(' + latex_names[species[0]] + ')')

        if('xlabel' not in kwargs):
            plt.xlabel(prop)

        self.apply_class_methods(plt, kwargs)

        plt.show()
