"""Analyze and plot contacts within lymph nodes"""
import itertools

import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import scipy.spatial as spatial
import mpl_toolkits.mplot3d.axes3d as p3
import mpl_toolkits.mplot3d.art3d as art3d
import matplotlib.gridspec as gridspec
from matplotlib.patches import Circle, PathPatch
from matplotlib.ticker import MaxNLocator

from utils import equalize_axis3d
from utils import track_identifiers


def find(tracks, n_Tcells=[10,20], n_DCs=[50,100], n_iter=10,
    ln_volume=0.125e9, contact_radius=10):
    """Simulate contacts within radius"""
    print('Simulating contacts {} times'.format(n_iter))

    if type(n_Tcells) == int:
        n_Tcells = [n_Tcells]

    if type(n_DCs) == int:
        n_DCs = [n_DCs]

    if type(contact_radius) != list:
        contact_radius = [contact_radius]

    if max(n_Tcells) > tracks['Track_ID'].unique().__len__():
        print('  Error: max. n_Tcells is larger than # of given tracks.')
        return

    contacts = pd.DataFrame()
    max_index = 0
    for n_run in range(n_iter):
        runs_contacts = pd.DataFrame()
        for cr, nT, nDC in itertools.product(contact_radius, n_Tcells, n_DCs):
            ln_r = (3*ln_volume/(4*np.pi))**(1/3)
            r = ln_r*np.random.rand(nDC)**(1/3)
            theta = np.random.rand(nDC)*2*np.pi
            phi = np.arccos(2*np.random.rand(nDC) - 1)
            DCs = pd.DataFrame({
                'X': r*np.sin(theta)*np.sin(phi),
                'Y': r*np.cos(theta)*np.sin(phi),
                'Z': r*np.cos(phi)})
            DC_tree = spatial.cKDTree(DCs)

            T_tracks = tracks[tracks['Track_ID'].isin(
                np.random.choice(tracks['Track_ID'].unique(), nT,
                replace=False))]

            free_Tcells = np.random.choice(T_tracks['Track_ID'].unique(),
                nT, replace=False)

            for time, positions in T_tracks.sort('Time').groupby('Time'):
                positions = positions[positions['Track_ID'].isin(free_Tcells)]
                positions = positions[np.linalg.norm(positions[['X', 'Y', 'Z']],
                    axis=1) < (ln_r + cr)]
                if positions.__len__() != 0:
                    Tcell_tree = spatial.cKDTree(positions[['X', 'Y', 'Z']])
                    new_contacts = DC_tree.query_ball_tree(
                        Tcell_tree, cr)
                    newly_bound_T_cells = []
                    for DC, DC_contacts in enumerate(new_contacts):
                        for T_cell_idx in DC_contacts:
                            runs_contacts.loc[max_index, 'Time'] = time
                            runs_contacts.loc[max_index, 'Run'] = n_run
                            runs_contacts.loc[max_index, 'Contact Radius'] = cr
                            runs_contacts.loc[max_index, 'Cell Numbers'] = \
                                '{} T cells, {} DCs'.format(nT, nDC)
                            runs_contacts.loc[max_index, 'Track ID'] = \
                                free_Tcells[T_cell_idx]
                            runs_contacts.loc[max_index, 'X'] = DCs.loc[DC, 'X']
                            runs_contacts.loc[max_index, 'Y'] = DCs.loc[DC, 'Y']
                            runs_contacts.loc[max_index, 'Z'] = DCs.loc[DC, 'Z']
                            max_index += 1
                            newly_bound_T_cells.append(T_cell_idx)
                    if len(newly_bound_T_cells) != len(list(set(newly_bound_T_cells))):
                        print('  Warning: T cell binding severall DCs!')
                    free_Tcells = np.delete(free_Tcells, newly_bound_T_cells)

        contacts = contacts.append(runs_contacts)

        print('  Run {} done.'.format(n_run+1))

    contacts.loc[max_index, 'Time'] = tracks['Time'].max()

    return contacts


def plot(contacts, parameters='Cell Numbers'):
    """Plot accumulation and final number of contacts"""
    sns.set(style='white')

    n_parameter_sets = len(contacts[parameters].unique()) - 1 # nan for t_end
    gs = gridspec.GridSpec(n_parameter_sets,2)
    final_ax = plt.subplot(gs[:,0])
    ax0 = plt.subplot(gs[1])

    final_ax.set_title('Final State')
    final_ax.set_ylabel('Percentage of Final Contacts')
    ax0.set_title('Dynamics')

    final_sum = contacts.groupby('Cell Numbers').count()['Time']
    order = list(final_sum.order().index.values)

    for label, _contacts in contacts.groupby(parameters):
        i = order.index(label)
        n_runs = _contacts['Run'].max() + 1
        label = '  ' + label + ' (n = {:.0f})'.format(n_runs)
        final_ax.text(i*2 - 0.5, 0, label, rotation=90, va='bottom')

        if i == 0:
            ax = ax0
        else:
            ax = plt.subplot(gs[2*i+1], sharex=ax0, sharey=ax0)

        if i < n_parameter_sets - 1:
            plt.setp(ax.get_xticklabels(), visible=False)
        else:
            ax.set_xlabel('Time [h]')

        color = sns.color_palette(n_colors=i+1)[-1]

        accumulation = _contacts.groupby(['Time', 'Run']).size().unstack().fillna(0).cumsum()
        runs_with_n_contacts = accumulation.apply(lambda x: x.value_counts(), axis=1).fillna(0)
        runs_with_n_contacts = runs_with_n_contacts[runs_with_n_contacts.columns[::-1]]
        runs_with_geq_n_contacts = runs_with_n_contacts.cumsum(axis=1)
        runs_with_geq_n_contacts.loc[contacts['Time'].max(), :] = \
            runs_with_geq_n_contacts.iloc[-1]

        for n_contacts in [n for n in runs_with_geq_n_contacts.columns if n > 0]:
            ax.fill_between(runs_with_geq_n_contacts[n_contacts].index/60, 0,
                runs_with_geq_n_contacts[n_contacts].values/n_runs*100,
                color=color, alpha=1/runs_with_n_contacts.columns.max())

            percentage = runs_with_geq_n_contacts[n_contacts].iloc[-1]/n_runs*100
            final_ax.bar(i*2, percentage, color=color,
                alpha=1/runs_with_n_contacts.columns.max())

            if n_contacts == runs_with_geq_n_contacts.columns.max():
                next_percentage = 0
            else:
                next_n = next(n for n in runs_with_geq_n_contacts.columns[::-1]
                    if n > n_contacts)
                next_percentage = runs_with_geq_n_contacts[next_n].iloc[-1]/n_runs*100

            percentage_diff = percentage - next_percentage
            if percentage_diff > 3:
                final_ax.text(i*2 + 0.38, percentage - percentage_diff/2 - 0.5,
                    int(n_contacts), ha='center', va='center')

    final_ax.set_xlim(left=-0.8)
    final_ax.set_xticks([])
    final_ax.set_ylim([0,100])
    ax.set_ylim([0,100])

    plt.tight_layout()
    plt.show()


def plot_situation(tracks, n_DCs=100, ln_volume=0.125e9, zoom=1):
    """Plot some tracks, DCs and volume"""
    sns.set_style('white')
    fig = plt.figure(figsize=(8,8))
    ax = fig.add_subplot(1,1,1, projection='3d')

    choice = np.random.choice(tracks['Track_ID'].unique(), 6*3)
    tracks = tracks[tracks['Track_ID'].isin(choice)]
    for _, track in tracks.groupby(track_identifiers(tracks)):
        ax.plot(track['X'].values, track['Y'].values, track['Z'].values)

    r = (3*ln_volume/(4*np.pi))**(1/3)*np.random.rand(n_DCs)**(1/3)
    theta = np.random.rand(n_DCs)*2*np.pi
    phi = np.arccos(2*np.random.rand(n_DCs) - 1)
    DCs = pd.DataFrame({
        'X': r*np.sin(theta)*np.sin(phi),
        'Y': r*np.cos(theta)*np.sin(phi),
        'Z': r*np.cos(phi)})
    ax.scatter(DCs['X'], DCs['Y'], DCs['Z'], color='y')

    r = (3*ln_volume/(4*np.pi))**(1/3)
    for i in ['x', 'y', 'z']:
        circle = Circle((0, 0), r, fill=False, linewidth=2)
        ax.add_patch(circle)
        art3d.pathpatch_2d_to_3d(circle, z=0, zdir=i)

    equalize_axis3d(ax, zoom)
    plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    import motility
    from remix import silly_tracks

    tracks = silly_tracks(25, 120)
    contacts = find(tracks, ln_volume=5e6)
    plot(contacts)
