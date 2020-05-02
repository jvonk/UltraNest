import numpy as np
import os
import matplotlib.pyplot as plt
from ultranest.mlfriends import ScalingLayer, AffineLayer, MLFriends
from numpy.testing import assert_allclose

here = os.path.dirname(__file__)


def test_region_sampling_scaling(plot=False):
    np.random.seed(1)
    upoints = np.random.uniform(0.2, 0.5, size=(1000, 2))
    upoints[:,1] *= 0.1
    
    transformLayer = ScalingLayer(wrapped_dims=[])
    transformLayer.optimize(upoints, upoints)
    region = MLFriends(upoints, transformLayer)
    region.apply_enlargement(nbootstraps=30)
    print("enlargement factor:", region.enlarge, 1 / region.enlarge)
    region.create_wrapping_geometry()
    nclusters = transformLayer.nclusters
    assert nclusters == 1
    assert np.allclose(region.unormed, region.transformLayer.transform(upoints)), "transform should be reproducible"
    assert region.inside(upoints).all(), "live points should lie near live points"
    if plot:
        plt.plot(upoints[:,0], upoints[:,1], 'x ')
        for method in region.sampling_methods:
            points, nc = method(nsamples=400)
            plt.plot(points[:,0], points[:,1], 'o ', label=str(method.__name__))
        plt.legend(loc='best')
        plt.savefig('test_regionsampling_scaling.pdf', bbox_inches='tight')
        plt.close()

    for method in region.sampling_methods:
        print("sampling_method:", method)
        newpoints, nc = method(nsamples=4000)
        lo1, lo2 = newpoints.min(axis=0)
        hi1, hi2 = newpoints.max(axis=0)
        assert 0.15 < lo1 < 0.25, (method.__name__, newpoints, lo1, hi1, lo2, hi2)
        assert 0.015 < lo2 < 0.025, (method.__name__, newpoints, lo1, hi1, lo2, hi2)
        assert 0.45 < hi1 < 0.55, (method.__name__, newpoints, lo1, hi1, lo2, hi2)
        assert 0.045 < hi2 < 0.055, (method.__name__, newpoints, lo1, hi1, lo2, hi2)
        assert region.inside(newpoints).mean() > 0.99, region.inside(newpoints).mean()

    region.maxradiussq = 1e-90
    assert np.allclose(region.unormed, region.transformLayer.transform(upoints)), "transform should be reproducible"
    assert region.inside(upoints).all(), "live points should lie very near themselves"


def test_region_sampling_affine(plot=False):
    np.random.seed(1)
    upoints = np.random.uniform(size=(1000, 2))
    upoints[:,1] *= 0.5
    
    transformLayer = AffineLayer(wrapped_dims=[])
    transformLayer.optimize(upoints, upoints)
    region = MLFriends(upoints, transformLayer)
    region.apply_enlargement(nbootstraps=30)
    print("enlargement factor:", region.enlarge, 1 / region.enlarge)
    region.create_wrapping_geometry()
    nclusters = transformLayer.nclusters
    assert nclusters == 1
    assert np.allclose(region.unormed, region.transformLayer.transform(upoints)), "transform should be reproducible"
    assert region.inside(upoints).all(), "live points should lie near live points"
    if plot:
        plt.plot(upoints[:,0], upoints[:,1], 'x ')
        for method in region.sampling_methods:
            points, nc = method(nsamples=400)
            plt.plot(points[:,0], points[:,1], 'o ', label=str(method.__name__))
        plt.legend(loc='best')
        plt.savefig('test_regionsampling_affine.pdf', bbox_inches='tight')
        plt.close()

    for method in region.sampling_methods:
        print("sampling_method:", method)
        newpoints, nc = method(nsamples=4000)
        lo1, lo2 = newpoints.min(axis=0)
        hi1, hi2 = newpoints.max(axis=0)
        assert 0 <= lo1 < 0.1, (method.__name__, newpoints, lo1, hi1, lo2, hi2)
        assert 0 <= lo2 < 0.1, (method.__name__, newpoints, lo1, hi1, lo2, hi2)
        assert 0.95 < hi1 <= 1, (method.__name__, newpoints, lo1, hi1, lo2, hi2)
        assert 0.45 <= hi2 < 0.55, (method.__name__, newpoints, lo1, hi1, lo2, hi2)
        assert region.inside(newpoints).all()

    region.maxradiussq = 1e-90
    assert np.allclose(region.unormed, region.transformLayer.transform(upoints)), "transform should be reproducible"
    assert region.inside(upoints).all(), "live points should lie very near themselves"

def test_region_ellipsoid(plot=False):
    np.random.seed(1)
    points = np.random.uniform(0.4, 0.6, size=(1000, 2))
    points[:,1] *= 0.5
    
    transformLayer = AffineLayer(wrapped_dims=[])
    transformLayer.optimize(points, points)
    region = MLFriends(points, transformLayer)
    region.apply_enlargement(nbootstraps=30)
    print("enlargement factor:", region.enlarge, 1 / region.enlarge)
    region.create_wrapping_geometry()
    nclusters = transformLayer.nclusters
    assert nclusters == 1
    
    bpts = np.random.uniform(size=(100, 2))
    mask = region.inside_ellipsoid(bpts)
    
    d = (bpts - region.ellipsoid_center)
    mask2 = np.einsum('ij,jk,ik->i', d, region.ellipsoid_invcov, d) <= region.enlarge
    
    assert_allclose(mask, mask2)

def test_region_mean_distances():
    np.random.seed(1)
    points = np.random.uniform(0.4, 0.6, size=(10000, 2))
    #points[:,1] *= 0.5
    mask = np.abs((points[:,0]-0.5)**2 + (points[:,1]-0.5)**2 - 0.08**2) < 0.02**2
    print('circle:', mask.sum())
    points = points[mask]
    mask = points[:,0] < 0.5
    print('half-circle:', mask.sum())
    points = points[mask]
    
    transformLayer = AffineLayer(wrapped_dims=[])
    transformLayer.optimize(points, points)
    region = MLFriends(points, transformLayer)
    region.apply_enlargement(nbootstraps=30)
    print("enlargement factor:", region.enlarge, 1 / region.enlarge)
    region.create_wrapping_geometry()
    meandist = region.compute_mean_pair_distance()
    
    t = transformLayer.transform(region.u)
    d = 0
    N = 0
    for i in range(len(t)):
        for j in range(i):
            d += ((t[i,:] - t[j,:])**2).sum()**0.5
            #print(i, j, t[i,:], t[j,:], ((t[i,:] - t[j,:])**2).sum())
            N += 1
    
    print((meandist, d, N, t))
    assert np.isclose(meandist, d / N), (meandist, d, N)

def loglike_funnel2d(theta):
    sigma = np.exp((theta[:,0] * 10 - 10) * 0.5)
    like = -0.5 * (((theta[:,1] - 0.5)/sigma)**2 + np.log(2 * np.pi * sigma**2))
    return like

def test_region_funnel(plot=False):
    np.random.seed(3)
    points = np.transpose([
        np.random.uniform(0., 1., size=4000),
        np.random.uniform(0., 1., size=4000),
    ])
    logp = loglike_funnel2d(points)
    indices = np.argsort(logp)
    points = points[indices[-1000:], :]
    points = points[::10, :]
    
    transformLayer = AffineLayer(wrapped_dims=[])
    transformLayer.optimize(points, points)
    region = MLFriends(points, transformLayer)
    region.apply_enlargement(nbootstraps=30)
    region.create_wrapping_geometry()
    samples, idx = region.sample(1000)

    cregion = MLFriends(points, transformLayer, sigma_dims=[0])
    cregion.apply_enlargement(nbootstraps=30)
    assert cregion.has_cones
    print('pads:', cregion.cone_radiisq)
    #print('number of cones:', cregion.cone_useful)
    cregion.create_wrapping_geometry()
    print('cone info:', cregion.cones)
    print(cregion.current_sampling_method)
    j, centers, sigma0, ymins, slopes, cone_radiussq = cregion.cones[0]
    print('xmin:', sigma0, 'slope:', slopes, 'offset0', np.exp(ymins)**0.5, 'padding:', cone_radiussq**0.5)
    assert j == 0
    #print('xmin:', xmin, points[:,0].min())
    np.testing.assert_allclose(sigma0, points[:,0].min())
    #print('ymin:', ymin, points[points[:,0].argmin(),1]**2)
    #np.testing.assert_allclose(ymin, points[points[:,0].argmin(),1])
    mask = cregion.inside(samples)
    csamples, cidx = cregion.sample(400)

    if plot:
        plt.plot(points[:,0], points[:,1], 'o ')
        plt.plot(samples[:,0], samples[:,1], 'x ')
        plt.plot(samples[mask,0], samples[mask,1], 's ', mew=1, mfc='None')

        sigma = np.linspace(0, 1, 4000)
        
        # predict the y values
        predict = np.exp((sigma.reshape((-1, 1)) - sigma0) * slopes.reshape((1, -1)) + ymins.reshape((1, -1)))
        predict[:,j] = 0
        z = (predict * cone_radiussq)**0.5
        plt.plot(sigma, (centers + z)[:,1])
        plt.plot(sigma, centers[1] + 0*sigma, '--')
        plt.plot(sigma, (centers - z)[:,1])
        
        plt.ylim(points[:,1].min(), points[:,1].max())
        plt.savefig('test_region_funnel_filter.pdf', bbox_inches='tight')
        plt.close()

    if plot:
        plt.plot(points[:,0], points[:,1], 'o ')
        plt.plot(samples[:,0], samples[:,1], 'x ')
        plt.plot(csamples[:,0], csamples[:,1], '^ ')
        plt.savefig('test_region_funnel_sample.pdf', bbox_inches='tight')
        plt.close()
    
    print('cone throughput:', mask.mean())
    assert mask.mean() < 0.85, mask.mean()

def loglike_funnelnd(theta):
    sigma = np.exp((theta[:,0].reshape((-1, 1)) * 10 - 10) * 0.5)
    like = -0.5 * (((theta[:,1:] - 0.5)/sigma)**2 + np.log(2 * np.pi * sigma**2)).sum(axis=1)
    return like

def get_cones(points):
    print("get_cones of:", points.shape)
    transformLayer = AffineLayer(wrapped_dims=[])
    transformLayer.optimize(points, points)
    cregion = MLFriends(points, transformLayer, sigma_dims=[0])
    cregion.apply_enlargement(nbootstraps=30)
    assert cregion.has_cones
    cregion.create_wrapping_geometry()
    print('cone info:', cregion.cones)
    return cregion.cones

def test_region_cone_activation(plot=False):
    np.random.seed(1)
    nsamples = 1000
    points = np.random.uniform(0., 1., size=(4000, 2))
    logp = loglike_funnel2d(points)
    assert logp.shape == (len(points),), (logp.shape, (len(points),))
    indices = np.argsort(logp)
    points = points[indices[-nsamples:], :]
    points_funnel2d = points
    
    points = np.random.uniform(0., 1., size=(4000000, 5))
    logp = loglike_funnelnd(points)
    assert logp.shape == (len(points),), (logp.shape, (len(points),))
    indices = np.argsort(logp)
    points = points[indices[-nsamples:], :]
    points_funnel5d = points
    #plt.plot(points_funnel5d[:,0], points_funnel5d[:,1], 'o ')
    #plt.show()
    
    points_uniform2d = np.random.uniform(0.4, 0.6, size=(nsamples, 2))
    points_uniform5d = np.random.uniform(0.4, 0.6, size=(nsamples, 5))
    points = np.random.uniform(0.4, 0.6, size=(10000, 2))
    mask = (points[:,0]-0.5)**2 + (points[:,1]-0.5)**2 < 0.1**2
    points_circle2d = points[mask,:][:nsamples,:]
    points = np.random.uniform(0.4, 0.6, size=(100000, 5))
    mask = (points[:,0]-0.5)**2 + (points[:,1]-0.5)**2 < 0.1**2
    points_circle5d = points[mask,:][:nsamples,:]
    
    v = np.random.multivariate_normal(np.zeros(2), [[0.01, 0.005], [0.005, 0.01]], size=nsamples)
    points_ellipse2d = v + 0.5
    
    print("Uniform 2d" + "*"*50)
    assert get_cones(points_uniform2d) == []
    print("Uniform 5d" + "*"*50)
    assert get_cones(points_uniform5d) == []
    print("Circle 2d" + "*"*50)
    assert get_cones(points_circle2d) == []
    print("Circle 5d" + "*"*50)
    assert get_cones(points_circle5d) == []
    print("Ellipse 2d" + "*"*50)
    assert get_cones(points_ellipse2d) == []
    print("Funnel 2d" + "*"*50)
    assert get_cones(points_funnel2d) != []
    print("Funnel 5d" + "*"*50)
    assert get_cones(points_funnel5d) != []

"""
def test_region_cone_consistency():
    datafile = os.path.join(os.path.dirname(__file__), 'conetestdata.npz')
    data = np.load(datafile)
    upoints = data['u']
    
    transformLayer = AffineLayer()
    transformLayer.optimize(upoints, upoints)
    region = MLFriends(upoints, transformLayer)
    region.apply_enlargement(nbootstraps=30)
    region.create_wrapping_geometry()
    assert region.inside(upoints).all(), region.inside(upoints)
"""

if __name__ == '__main__':
    #test_region_funnel(plot=True)
    test_region_cone_activation()
    #test_region_sampling_scaling(plot=True)
    #test_region_sampling_affine(plot=True)
    #test_region_cone_consistency()
